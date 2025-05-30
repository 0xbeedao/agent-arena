from typing import Optional

from sqlmodel import Field
from sqlmodel import Session
from statemachine import State

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob
from agentarena.models.job import JobResponse
from agentarena.models.job import JobState
from agentarena.scheduler.services.queue_service import QueueService
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
        actor_url: str = Field(description="url of actor service"),
        arena_url: str = Field(description="url of arena server"),
        queue_service: QueueService = Field(description="Queue Service"),
        message_broker: MessageBroker = Field(),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        assert arena_url
        assert actor_url
        self.actor_url = actor_url
        self.arena_url = arena_url
        self.queue_service = queue_service
        self.message_broker = message_broker
        self.logging = logging
        self.log = logging.get_logger("service")

    async def poll_and_process(self, session: Session) -> bool:
        """
        Poll the queue for jobs and process them.
        """
        job = await self.queue_service.get_next(session)
        if job is None:
            # self.log.debug("No job found in queue")
            return False

        self.log.info("Processing job", job_id=getattr(job, "id", None))
        await self.process_job(job, session)
        return True

    async def process_job(self, job: CommandJob, session: Session):
        """
        Process a single job using the request state machine.
        """
        log = self.log.bind(method="process_job", job=job.id)
        log.info("processing")
        machine = RequestMachine(
            job,
            arena_url=self.arena_url,
            actor_url=self.actor_url,
            logging=self.logging,
            message_broker=self.message_broker,
        )
        await machine.activate_initial_state()  # type: ignore
        await machine.start_request("request")

        # machine will now be in a final state
        state: State = machine.current_state
        if not state.final:
            log.warn(f"Invalid final state: {state.value}")
            return False
        obj = machine.response_object
        curr = state.value
        if curr == RequestState.FAIL.value:
            return await self.handle_fail(job, obj, session)
        elif curr == RequestState.WAITING.value:
            return await self.handle_waiting(job, obj, session)
        elif curr == RequestState.COMPLETE.value:
            return await self.handle_complete(job, obj, session)
        else:
            raise Exception(f"Invalid state {state.value}")

    async def handle_complete(
        self, job: CommandJob, response: Optional[JobResponse], session: Session
    ):
        """
        Handle a completed job.
        """
        self.log.info("Job complete", job=getattr(job, "id", None))
        data = None
        if response is not None:
            data = response.model_dump_json()
        message: str = ""
        if response is not None and response.message is not None:
            message = response.message
        result = await self.queue_service.update_state(
            job.id,
            JobState.COMPLETE,
            session,
            message=message,
            data=data,
        )
        return result is not None

    async def handle_fail(
        self, job: CommandJob, response: Optional[JobResponse], session: Session
    ):
        """
        Handle a failed job.
        """
        self.log.info(
            "Job failed",
            job=getattr(job, "id", None),
            error=response.message if response else "none",
        )
        message: str = ""
        if response is not None and response.message is not None:
            message = response.message
        result = await self.queue_service.update_state(
            job.id, JobState.FAIL, session, message=message
        )

        return result is not None

    async def handle_waiting(
        self, job: CommandJob, response: Optional[JobResponse], session: Session
    ):
        """
        Handle a waiting job (requeue).
        """
        self.log.info("Job waiting, requeueing", job=getattr(job, "id", None))
        delay = 0
        if response is not None and response.delay is not None:
            delay = response.delay
        result = await self.queue_service.requeue_job(job, session, delay=delay)
        return result is not None
