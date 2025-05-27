import asyncio
from enum import Enum
from typing import Dict
from typing import List

from sqlmodel import Field
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Participant
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.event import JobEvent
from agentarena.models.job import CommandJob
from agentarena.models.job import JobState
from agentarena.scheduler.services.queue_service import QueueService


class ReadyState(Enum):
    INIT = "init"
    POLLING = "polling"
    READY = "ready"
    FAIL = "fail"


READY_CHECK = "READY_CHECK"


class ReadyMachine(StateMachine):
    """
    State machine for doing a poll of all Participants for "ready"
    """

    init = State(ReadyState.INIT.value, initial=True)
    polling = State(ReadyState.POLLING.value)
    fail = State(ReadyState.FAIL.value, final=True)
    ready = State(ReadyState.READY.value, final=True)

    check = init.to(polling)
    timeout_fail = polling.to(fail)
    are_we_done = (
        polling.to(ready, cond="all_checked_in", unless="any_failed")
        | polling.to(polling, unless="all_checked_in")
        | polling.to(fail, cond="any_failed")
    )

    def __init__(
        self,
        participants: List[Participant] = Field(description="Particants to poll"),
        queue_service: QueueService = Field(description="the queue service"),
        timeout_seconds: int = Field(
            description="seconds to wait for all player response"
        ),
        logging: LoggingService = Field(description="Logging factory"),
    ):
        self.participants = participants
        self.q = queue_service
        self.timeout_seconds = timeout_seconds
        self.log = logging.get_logger("machine", participants=len(participants))
        self._jobs: Dict[str, Participant] = {}
        self.checked_in: List[str] = []
        self.failed: List[str]

    async def _timeout_coroutine(self):
        try:
            await asyncio.sleep(self.timeout_seconds)
            self.log.warn(f"Polling timed out after {self.timeout_seconds} seconds.")
            await self.timeout_fail("")
        except asyncio.CancelledError:
            # Expected: task cancelled when polling ends
            pass

    async def _cancel_timeout_task(self):
        if getattr(self, "_timeout_task", None):
            self._timeout_task.cancel()
            try:
                await self._timeout_task
            except asyncio.CancelledError:
                pass
            self._timeout_task = None

    def all_checked_in(self):
        return len(self.participants) == len(self.checked_in)

    def any_failed(self):
        return len(self.failed) > 0

    async def on_enter_ready(self):
        await self._cancel_timeout_task()

    async def on_enter_fail(self):
        await self._cancel_timeout_task()

    async def on_enter_polling(self):
        self.log.info("Starting polling")
        for p in self.participants:
            job: CommandJob = self.make_health_request_job(p)
            # TODO: needs to use NATS
            # await self.q.send_job(job)
            self._jobs[job.id] = p
        self.log.info("Requests sent to queue")
        self._timeout_task = asyncio.create_task(self._timeout_coroutine())

    async def ready_check(self, event: JobEvent):
        log = self.bind(event=event)
        if event.job_id in self._jobs:
            log.info("Got valid event")
            participant: Participant = self._jobs[event.job_id]
            if event.state == JobState.FAIL.value:
                self.failed.append(participant.id)
            else:
                if participant.id not in self.checked_in:
                    self.checked_in.append(participant.id)
                else:
                    self.log.info("Already had this one checked in, ignoring")
            self.are_we_done("")
        else:
            log.debug("not interested")
