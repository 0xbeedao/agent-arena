from dependency_injector.wiring import Provide
from fastapi import Depends
from httpx import Response

from agentarena.containers import Container
from agentarena.models.job import BaseAsyncJobResponse
from agentarena.models.job import JsonRequestJob
from agentarena.statemachines.request_machine import RequestMachine


class RequestService:
    """
    Service for handling async requests using the RequestMachine state machine.

    Flow:
    - Poll jobs from the queue.
    - For each job, run the request state machine.
    - On COMPLETE: send payload to calling service.
    - On FAIL: send rejection to calling service.
    - On WAITING: reject job and requeue.
    """

    def __init__(
        self,
        queue_service=Depends(Provide[Container.job_q_service]),
        http_client_factory=Depends(Provide[Container.http_client]),
        logging=None,
    ):
        """
        :param queue_service: Service for queue operations (get, requeue jobs).
        :param http_client: Service or function to send HTTP requests.
        :param result_handler: Service or function to handle results (payload/rejection).
        """
        self.queue_service = queue_service
        self.http_client = http_client_factory()
        self.log = logging.get_logger("requestservice")

    def poll_and_process(self):
        """
        Poll the queue for jobs and process them.
        """
        job: JsonRequestJob = self.queue_service.get_job()
        if job is None:
            self.log.debug("No job found in queue")
            return

        self.log.info("Processing job", job_id=getattr(job, "id", None))
        self.process_job(job)

    def process_job(self, job: JsonRequestJob):
        """
        Process a single job using the request state machine.
        """
        machine = RequestMachine(job=job)
        machine.get_job()  # IDLE -> REQUEST
        machine.start_request()  # REQUEST -> REQUESTING

        response: Response = None

        # send the request
        try:
            method = job.method
            response = self.http_client[method](job.url, data=job.payload)
            if response.status_code >= 400:
                machine.http_error()  # REQUESTING -> FAIL
                self.handle_fail(job, response)
                return
            else:
                machine.http_ok()  # REQUESTING -> RESPONSE
        except Exception as e:
            machine.http_error()
            self.handle_fail(job, error=e)
            return

        # Process response
        if not self.is_response_valid(response):
            machine.malformed_response()  # RESPONSE -> FAIL
            self.handle_fail(job, response)
            return

        state = self.get_response_state(response)
        if state == "complete":
            machine.state_complete()  # RESPONSE -> COMPLETE
            self.handle_complete(job, response)
        elif state == "pending":
            machine.state_pending()  # RESPONSE -> WAITING
            self.handle_waiting(job, response)
        elif state == "failure":
            machine.state_failure()  # RESPONSE -> FAIL
            self.handle_fail(job, response)
        else:
            machine.malformed_response()  # RESPONSE -> FAIL
            self.handle_fail(job, response)

    def handle_complete(self, job, response):
        """
        Handle a completed job.
        """
        self.log.info("Job complete", job_id=getattr(job, "id", None))
        self.result_handler.send_payload(job, response)

    def handle_fail(self, job, response=None, error=None):
        """
        Handle a failed job.
        """
        self.log.info("Job failed", job_id=getattr(job, "id", None), error=error)
        self.result_handler.send_rejection(job, response, error)

    def handle_waiting(self, job, response):
        """
        Handle a waiting job (requeue).
        """
        self.log.info("Job waiting, requeueing", job_id=getattr(job, "id", None))
        self.queue_service.requeue_job(job)

    def is_response_valid(self, response):
        """
        Validate the response (placeholder).
        """
        # Implement actual validation logic
        return response is not None

    def get_response_state(self, response: BaseAsyncJobResponse):
        """
        Determine the state from the response (placeholder).
        Should return one of: "complete", "pending", "failure"
        """
        return "failure" if response is None else response.status

    def wakeup_job(self, job):
        """
        Handle a wakeup event for a waiting job.
        """
        machine = RequestMachine(job=job)
        machine.wakeup()  # WAITING -> REQUEST
        self.process_job(job)
