from datetime import datetime
from typing import Any
from typing import Dict
from typing import Mapping
from typing import Optional

from nats.aio.msg import Msg
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import select

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import SubscribingService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobHistory
from agentarena.models.job import CommandJobHistoryCreate
from agentarena.models.job import JobResponse
from agentarena.models.job import JobState

FINAL_STATES = [JobState.FAIL.value, JobState.COMPLETE.value]
ALL_STATES = [state.value for state in JobState]


def make_response(job: CommandJob, data: Dict, message: str):
    return JobResponse(
        channel=job.channel,
        data=data,  # type: ignore
        delay=0,
        method=job.method,
        url=job.url,
        job_id=job.id,
        message=message,
        state=job.state or JobState.COMPLETE.value,
    )


class QueueService(SubscribingService):
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
        to_subscribe = [("arena.request.job", self.add_job_from_message)]
        # setup subscriptions
        super().__init__(to_subscribe, self.log)

    async def drain(self, session, message=""):
        log = self.log.bind(method="drain")
        log.info("Draining queue")
        job = await self.get_next(session)
        while job is not None:
            await self.update_state(job.id, "fail", session, message=message)
        log.info("drain complete")

    async def add_job(self, job: CommandJob, session: Session):
        if job.state == JobState.IDLE.value:
            job.started_at = 0
            job.finished_at = 0
        created, response = await self.job_service.create(job, session)
        if response.success:
            return created
        return None

    async def add_job_from_message(self, msg: Msg):
        self.log.info("add job from message", data=msg.data)
        job = None
        try:
            job = CommandJob.model_validate_json(msg.data)
        except Exception as e:
            self.log.error("Could not accept job", e)

        if job:
            msg.Ack()
            with self.job_service.get_session() as session:
                self.log.info("Adding job from message", job=job)
                await self.add_job(job, session)
        else:
            self.log.info("unexpected error making job from message")

    async def get_next(self, session: Session) -> CommandJob | None:
        now = int(datetime.now().timestamp())
        stmt = (
            select(CommandJob)
            .where(CommandJob.state == JobState.IDLE.value)
            .where(CommandJob.send_at <= now)
            .order_by(CommandJob.created_at)  # type: ignore
        )
        next = session.exec(stmt).first()

        if not next:
            return None
        updated_job = await self.update_state(
            next.id, JobState.REQUEST.value, session, message="picked up from queue"
        )
        self.log.debug(
            "returning next job", job=updated_job.id if updated_job else "none"
        )
        return updated_job

    async def requeue_job(
        self,
        job_id,
        session,
        message="requeue",
        data: Optional[Mapping[str, Any]] = {},
        delay: int = 0,
    ) -> CommandJob | None:
        return await self.update_state(
            job_id,
            JobState.IDLE.value,
            session,
            message=message,
            data=data,
            delay=delay,
        )

    async def revalidate_batch(self, batch: CommandJob, session: Session):
        current_state = batch.state
        if current_state == JobState.IDLE.value:
            # this batch is waiting to be picked up for final run
            return False

        log = self.log.bind(batch=batch.id)
        log.info("Revalidating")
        info = []
        ct = 0
        complete = True
        failed = False
        for c in batch.children:
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
            await self.update_state(batch.id, state, session, message=",".join(info))
            return True
        return True

    async def send_final_message(
        self,
        job: CommandJob,
        session,
        message: str = "",
        data: Optional[Mapping[str, Any]] = {},
    ):
        log = self.log.bind(job=job.id)
        # if this is a batch, when we send the final message, we want all the child messages as well.
        log.debug("sending final message")
        res = make_response(job, data, message)  # type: ignore
        child_data = []
        stmt = select(CommandJob).where(CommandJob.parent_id == job.id)
        children = session.exec(stmt)

        for child in children:
            log.debug("adding child response", child=child.id)
            stmt = (
                select(CommandJobHistory)
                .where(CommandJobHistory.to_state == child.state)
                .order_by(CommandJobHistory.created_at)  # type: ignore
            )
            rows = session.exec(stmt).all()
            last = rows.pop() if rows else None
            data = last.data if last else {}
            child_data.append(make_response(child, data, message))

        res.child_data = child_data

        await self.message_broker.send_response(job.channel, res)

    async def update_parent_states(self, job: CommandJob, session: Session):
        log = self.log.bind(job=job.id)
        if not job.parent_id:
            log.info("No parent to update")
            return False

        pid = job.parent_id
        log.info("Parent is a batch, sending for revalidation", parent=pid)
        parent = session.get(CommandJob, pid)
        if not parent:
            log.warn("unexpected couldn't get parent")
            return False
        return await self.revalidate_batch(parent, session)

    async def update_state(
        self,
        job_id: str,
        state: str,
        session: Session,
        message: str = "",
        data: Optional[Mapping[str, Any]] = {},
        delay=0,
    ) -> CommandJob | None:

        if not state in ALL_STATES:
            self.log.warn(f"Invalid state: {state}")
            return None

        log = self.log.bind(method="update_state", state=state, job_id=job_id)

        job, response = await self.job_service.get(job_id, session)

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
            CommandJobHistoryCreate(
                job_id=job.id,
                from_state=old_state,
                to_state=state,
                message=message,
                data=data,  # type: ignore
            ),
            session,
        )
        sent, response = await self.job_service.update(job.id, job, session)
        # send message if any
        if not response.success:
            sent = None

        if response.success and state in FINAL_STATES and sent is not None:
            log.debug("Sending message for final state")
            await self.send_final_message(sent, session, message=message, data=data)

        if sent and sent.parent_id:
            log.info("Starting update_parent_states for child request")
            await self.update_parent_states(sent, session)

        if sent:
            return sent

        return None
