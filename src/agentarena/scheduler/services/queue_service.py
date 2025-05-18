from datetime import datetime
from typing import Any, List, Mapping, Optional

from pydantic import Field

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob, CommandJobRequest, JobResponse
from agentarena.models.job import CommandJobHistory
from agentarena.models.job import JobState
from agentarena.models.job import UrlJobRequest
from agentarena.core.services.model_service import ModelService

FINAL_STATES = [JobState.FAIL.value, JobState.COMPLETE.value]
ALL_STATES = [state.value for state in JobState]


class QueueService:
    """
    Provides DB backed job queue services
    """

    def __init__(
        self,
        history_service: ModelService[CommandJobHistory] = Field(
            description="Job History Service"
        ),
        job_service: ModelService[CommandJob] = Field(description="job model service"),
        message_broker: MessageBroker = Field(description="Message broker"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.history_service = history_service
        self.job_service = job_service
        self.message_broker = message_broker
        self.log = logging.get_logger("service")

    async def drain(self, message=""):
        log = self.log.bind(method="drain")
        log.info("Draining queue")
        job = await self.get_next()
        while job is not None:
            await self.update_state(job.id, "fail", message=message)
        log.info("drain complete")

    async def add_job(self, req: CommandJobRequest):
        """
        NATS refactor notes - this needs to be executed on the consuming side.
        """
        job = req.to_job()
        if not job.id:
            job.started_at = 0
            job.finished_at = 0
        created, response = await self.job_service.create(job)
        if response.success:
            return created
        return None

    async def get_next(self) -> CommandJob | None:
        next = await self.job_service.get_where(
            "state = :idle and send_at <= :now",
            {
                "idle": JobState.IDLE.value,
                "now": int(datetime.now().timestamp()),
            },
            order_by="priority asc, updated_at asc, created_at asc",
            limit=1,
        )
        if not next:
            return None
        job = next[0]
        updated_job = await self.update_state(
            job.id, JobState.REQUEST.value, "picked up from queue"
        )
        self.log.info(
            "returning next job", job=updated_job.id if updated_job else "none"
        )
        return updated_job

    async def requeue_job(
        self,
        job_id,
        message="requeue",
        data: Optional[Mapping[str, Any]] = {},
        delay: int = 0,
    ) -> CommandJob | None:
        return await self.update_state(
            job_id, JobState.IDLE.value, message=message, data=data, delay=delay
        )

    async def revalidate_batch(self, batch: CommandJob):
        current_state = batch.state
        if current_state == JobState.IDLE.value:
            # this batch is waiting to be picked up for final run
            return False

        log = self.log.bind(batch=batch.id)
        pid = batch.id
        log.info("Revalidating")
        children = await self.job_service.get_where("parent_id = :pid", {"pid": pid})
        info = []
        ct = 0
        complete = True
        failed = False
        for c in children:
            ct += 1
            if c.state == JobState.FAIL.value:
                failed = True
                info.append(f"Child {c.id} in FAIL - batch fail")
            if c.state != JobState.COMPLETE.value:
                complete = False
                info.append(f"Child {c.id} is in {c.state} - batch pending")

        if ct == 0:
            log.info("This is an invalid batch, as it has no children")
            return False

        state = batch.state
        if failed:
            state = JobState.FAIL.value
        elif complete:
            if batch.url:
                # this will kick off the final request
                state = JobState.IDLE.value

        log.debug("info from validation", info=info, state=state)
        if state and state != batch.state:
            # this will kick off revalidation of parents as well, if needed
            await self.update_state(batch.id, state, ",".join(info))
            return True
        return True

    async def send_final_message(
        self, job: CommandJob, message: str = "", data: Optional[Mapping[str, Any]] = {}
    ):
        res = JobResponse(
            job_id=job.id,
            delay=0,
            message=message,
            state=job.state or JobState.COMPLETE.value,
            data=data,
        )
        await self.message_broker.send_response(job.channel, res)

    async def update_parent_states(self, job: CommandJob):
        log = self.log.bind(job=job.id)
        if not job.parent_id:
            log.info("No parent to update")
            return False

        pid = job.parent_id
        log = log.bind(parent=pid)
        parent, response = await self.job_service.get(pid)
        if parent is None or not response.success:
            log.warn("Couldn't get parent, aborting")
            return False
        log.info("Parent is a batch, sending for revalidation")
        return await self.revalidate_batch(parent)

    async def update_state(
        self,
        job_id: str,
        state: str,
        message: str = "",
        data: Optional[Mapping[str, Any]] = {},
        delay=0,
    ) -> CommandJob | None:

        if not state in ALL_STATES:
            self.log.warn(f"Invalid state: {state}")
            return None

        log = self.log.bind(method="update_state", state=state, job_id=job_id)

        job, response = await self.job_service.get(job_id)

        if job is None or not response.success:
            log.warn("No such job")
            return None

        old_state = job.state or JobState.IDLE.value
        job.state = state
        log = log.bind(state=state)
        sent = None
        if state in FINAL_STATES:
            log.info("final state for job")
            job.finished_at = int(datetime.now().timestamp())
        elif old_state != job.state:
            if state == JobState.REQUEST.value:
                log.info("Starting job, setting started_at")
                job.started_at = int(datetime.now().timestamp())
            elif state == JobState.IDLE.value:
                # requeue
                job.send_at = int(datetime.now().timestamp() + delay)
            else:
                log.info("job state updated to a non-final state, saving")

        await self.history_service.create(
            CommandJobHistory(
                job_id=job.id,
                from_state=old_state,
                to_state=state,
                message=message,
                data=data,
            )
        )
        sent, response = await self.job_service.update(job)
        # send message if any
        if not response.success:
            sent = None

        if response.success and state in FINAL_STATES and sent is not None:
            log.debug("Sending message for final state")
            await self.send_final_message(sent, message=message, data=data)

        if sent and sent.parent_id:
            log.info("Starting update_parent_states for child request")
            await self.update_parent_states(sent)

        return sent
