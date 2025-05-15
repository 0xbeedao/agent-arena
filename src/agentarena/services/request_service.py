from pydantic import Field
from statemachine import State

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob
from agentarena.models.job import JobResponse
from agentarena.models.job import JobState
from agentarena.services.queue_service import QueueService
from agentarena.statemachines.request_machine import RequestMachine
from agentarena.statemachines.request_machine import RequestState


class RequestService:
    """
    Service for handling queued async requests using the RequestMachine state machine.

    Flow:
    - Poll jobs from the queue.
    - For each job, run the request state machine.
    - On COMPLETE: send payload to calling service.
    - On FAIL: send rejection to calling service.
    - On WAITING: reject job and requeue.
    """

    def __init__(
        self,
        arena_url: str = Field(description="url of arena server"),
        queue_service: QueueService = None,
        logging: LoggingService = Field(description="Logger factory"),
    ):
        assert arena_url
        self.arena_url = arena_url
        self.queue_service = queue_service
        self.logging = logging
        self.log = logging.get_logger("service")

    async def poll_and_process(self) -> bool:
        """
        Poll the queue for jobs and process them.
        """
        job = await self.queue_service.get_next()
        if job is None:
            # self.log.debug("No job found in queue")
            return False

        self.log.info("Processing job", job_id=getattr(job, "id", None))
        await self.process_job(job)
        return True

    async def process_job(self, job: CommandJob):
        """
        Process a single job using the request state machine.
        """
        log = self.log.bind(method="process_job", job=job.id)
        log.info("processing")
        machine = RequestMachine(job, logging=self.logging, arena_url=self.arena_url)
        await machine.activate_initial_state()
        await machine.start_request()

        # machine will now be in a final state
        state: State = machine.current_state
        if not state.final:
            log.warn(f"Invalid final state: {state.value}")
            return False
        obj = machine.response_object
        state = state.value
        if state == RequestState.FAIL.value:
            return await self.handle_fail(job, obj)
        elif state == RequestState.WAITING.value:
            return await self.handle_waiting(job, obj)
        elif state == RequestState.COMPLETE.value:
            return await self.handle_complete(job, obj)
        else:
            raise Exception(f"Invalid state {state.value}")

    async def handle_complete(self, job, response: JobResponse):
        """
        Handle a completed job.
        """
        self.log.info("Job complete", job=getattr(job, "id", None))
        result = await self.queue_service.update_state(
            job.id,
            JobState.COMPLETE.value,
            message=response.message,
            data=response.model_dump_json(),
        )
        return result is not None

    async def handle_fail(self, job, response: JobResponse):
        """
        Handle a failed job.
        """
        self.log.info(
            "Job failed",
            job=getattr(job, "id", None),
            error=response.message if response else "none",
        )
        result = await self.queue_service.update_state(
            job.id, JobState.FAIL.value, response.message if response else "none"
        )

        return result is not None

    async def handle_waiting(self, job, response: JobResponse):
        """
        Handle a waiting job (requeue).
        """
        self.log.info("Job waiting, requeueing", job=getattr(job, "id", None))
        result = await self.queue_service.requeue_job(job, delay=response.delay)
        return result is not None
