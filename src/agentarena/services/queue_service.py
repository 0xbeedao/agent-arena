import json
from datetime import datetime
from typing import List

from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.event import JobEvent
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobHistory
from agentarena.models.job import JobCommandType
from agentarena.models.job import JobState
from agentarena.models.job import JsonRequestSummary
from agentarena.services.event_bus import IEventBus
from agentarena.services.model_service import ModelService

FINAL_STATES = [JobState.FAIL.value, JobState.COMPLETE.value]
ALL_STATES = [state.value for state in JobState]


class QueueService:
    """
    Provides DB backed job queue services
    """

    def __init__(
        self,
        event_bus: IEventBus = Field(description="Event Bus"),
        history_service: ModelService[CommandJobHistory] = Field(
            description="Job History Service"
        ),
        job_service: ModelService[CommandJob] = Field(description="job model service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.event_bus = event_bus
        self.history_service = history_service
        self.job_service = job_service
        self.log = logging.get_logger(module="queue_service")

    async def drain(self, message=""):
        log = self.log.bind(method="drain")
        log.info("Draining queue")
        job = await self.get_next()
        while job is not None:
            self.update_state(job.id, "fail", message=message)
        log.info("drain complete")

    async def send_batch(
        self, job: CommandJob, requests: List[JsonRequestSummary]
    ) -> CommandJob:
        batch_job = await self.send_job(job)
        jobs = batch_job.make_batch_requests(requests)
        # set this job to "BATCH" - which makes it not respond to "get_next" requests
        # and allows us to identify which jobs need updating when children complete
        updated_job = await self.update_state(
            batch_job.id, JobState.REQUEST.value, message="queuing batch"
        )
        for job in jobs:
            await self.send_job(job)
        return updated_job

    async def send_job(self, job: CommandJob):
        if job.id is None:
            job.started_at = 0
            job.finished_at = 0
        created, response = await self.job_service.create(job)
        if response.success:
            return created
        return None

    async def get_next(self, command=JobCommandType.REQUEST.value) -> CommandJob:
        next = await self.job_service.get_where(
            "state = :idle and send_at < :now and command=:cmd",
            {
                "cmd": command,
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
        self.log.info("returning next job", job=updated_job.id)
        return updated_job

    async def publish_final_event(self, job: CommandJob, message: str, data: str):
        log = self.log.bind(job=job.id, method="publish_final_event")
        if job.event is None or len(job.event) == 0:
            log.warn("Invalid - no event defined")
            return

        response = None
        event: JobEvent = None
        if data:
            try:
                response = json.loads(data)
                log.info("sending event with full response data")
                event = JobEvent.from_job_and_response(job, response)
            except Exception as e:
                log.warn("couldn't parse response data", data=data)

        if event is None:
            log.info("Creating default event")
            event = JobEvent(
                job_id=job.id,
                name=job.event,
                data={},
                command=job.command,
                message=message,
                state=job.state,
            )

        await self.event_bus.publish(event)

    async def requeue_job(
        self, job_id, message="requeue", data="", delay: int = 0
    ) -> CommandJob:
        return await self.update_state(
            job_id, JobState.IDLE.value, message=message, data=data, delay=delay
        )

    async def revalidate_batch(self, batch: CommandJob):
        if batch.command != JobCommandType.BATCH.value:
            self.log.warn("Not a batch", batch=batch.id, command=batch.command)
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
                info.append(f"Child #{c.id} in FAIL - batch fail")
            if c.state != JobState.COMPLETE.value:
                complete = False
                info.append(f"Child #{c.id} is in {c.state} - batch pending")

        if ct == 0:
            log.info("This is an invalid batch, as it has no children")
            return False

        state = batch.state
        if failed:
            state = JobState.FAIL.value
        elif complete:
            state = JobState.COMPLETE.value

        log.debug("info from validation", info=info, state=state)
        if state != batch.state:
            # this will kick off revalidation of parents as well, if needed
            await self.update_state(batch.id, state, ",".join(info))
            return True
        return True

    async def update_parent_states(self, job: CommandJob):
        log = self.log.bind(job=job.id)
        if not job.parent_id:
            log.info("No parent to update")
            return False

        pid = job.parent_id
        log = log.bind(parent=pid)
        parent, response = await self.job_service.get(pid)
        if not response.success:
            log.warn("Couldn't get parent, aborting")
            return False
        if parent.command == JobCommandType.BATCH.value:
            log.info("Parent is a batch, sending for revalidation")
            return await self.revalidate_batch(parent)
        return True

    async def update_state(
        self, job_id: str, state: str, message: str = "", data="", delay=0
    ) -> CommandJob:

        if not state in ALL_STATES:
            log.warn(f"Invalid state: {state}")
            return False

        log = self.log.bind(method="update_state", state=state, job_id=job_id)

        job, response = await self.job_service.get(job_id)

        if job is None or not response.success:
            log.warn("No such job")
            return None

        old_state = job.state
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
        if not response.success:
            sent = None

        if state in FINAL_STATES and sent.event is not None and len(sent.event) > 0:
            await self.publish_final_event(sent, message, data)

        if sent.parent_id:
            log.info("Starting update_parent_states for child request")
            await self.update_parent_states(sent)

        return sent
