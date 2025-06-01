"""
The Contest State Machine
"""

import json
from typing import Any
from typing import Dict
from typing import List
from typing import Optional

from nats.aio.msg import Msg
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestRoundState
from agentarena.arena.models import ContestState
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobBatchRequest
from agentarena.models.job import UrlJobRequest

from .roundmachine import RoundMachine
from .setupmachine import SetupMachine


class ContestMachine(StateMachine):
    """
    Top-level Contest machine that manages the overall contest flow.

    States:
    - Starting: Initial state
    - Role_Call: State for checking participant roles
    - Setup_Arena: State for setting up the arena
    - In_Round: State for round
    - Check_End: State for checking end conditions
    - Fail: State for handling errors
    - Complete: Final state
    """

    starting = State("starting", initial=True)
    role_call = State("role_call")
    setup_arena = State("setup_arena")
    in_round = State("in_round")
    check_end = State("check_end")
    fail = State("fail", final=True)
    complete = State("complete", final=True)

    # Transitions
    start_contest = starting.to(role_call)
    roles_present = role_call.to(setup_arena)
    roles_error = role_call.to(fail)
    setup_done = setup_arena.to(in_round)
    setup_error = setup_arena.to(fail)
    round_complete = in_round.to(check_end)
    round_error = in_round.to(fail)
    contest_complete = check_end.to(complete)
    more_rounds = check_end.to(in_round)

    def __init__(
        self,
        contest: Contest,
        message_broker: MessageBroker,
        round_service: ModelService[ContestRound, ContestRoundCreate],
        uuid_service: UUIDService,
        log: ILogger,
    ):
        """Initialize the contest machine."""
        self._setup_machine = None
        self._round_machine = None
        self.contest = contest
        self.message_broker = message_broker
        self.round_service = round_service
        self.uuid_service = uuid_service
        self.log = log
        self.subscriptions = {}
        state = contest.state.value if contest.state else ContestState.STARTING.value
        if state == ContestState.CREATED.value:
            state = ContestState.STARTING.value
        super().__init__(start_value=state)

    async def handle_role_call(self, msg: Msg):
        """
        Handle the role call message.

        This method is called when a role call message is received.
        It processes the message and transitions to the next state if needed.
        """
        self.log.info("Handling role call message", msg=msg)
        sub = self.subscriptions.get(msg.subject)
        if sub:
            self.log.debug(f"Unsubscribing from {msg.subject}")
            await sub.unsubscribe()
            del self.subscriptions[msg.subject]
        obj = None
        if not msg.data:
            self.log.error("Received empty role call message", msg=msg)
            return
        try:
            obj = json.loads(msg.data.decode("utf-8"))
        except json.JSONDecodeError as e:
            self.log.error("Failed to decode role call message", error=str(e), msg=msg)
            return

        job_state = obj.get("state", None)
        if job_state is None:
            self.log.error("Role call message does not contain a state", msg=msg)
            return
        job_id = obj.get("job_id", "unknown job Id")
        if job_state == JobState.COMPLETE.value:
            self.log.info("Role call complete, transitioning to setup arena")
            try:
                await self.roles_present(job_id)
            except Exception as e:
                self.log.error(
                    "Failed to transition from role_call to setup_arena",
                    error=str(e),
                    exc_info=True,
                    job_id=job_id,
                    contest_id=self.contest.id,
                    current_state=self.current_state.id,
                )
                await self.roles_error(job_id)
        elif job_state == JobState.FAIL.value:
            self.log.error("Role call failed, transitioning to fail state")
            await self.roles_error(job_id)
        else:
            self.log.warn(
                f"Role call message in unexpected state: {job_state}, ignoring message"
            )
            # Optionally, you could handle other states or log them
            return

    async def on_enter_role_call(self):
        """Called when entering the InSetup state."""
        job_id = self.uuid_service.make_id()
        channel = f"arena.contest.{self.contest.id}.role_call"
        if self.subscriptions.get(channel):
            self.log.debug(f"Already subscribed to {channel}, skipping subscription")
        else:
            sub = await self.message_broker.client.subscribe(
                channel, cb=self.handle_role_call
            )
            self.log.debug(f"Subscribed to {channel}")
            self.subscriptions[channel] = sub

        batchJob = CommandJob(
            id=job_id,
            channel=channel,
            method="FINAL",
            send_at=0,
            priority=5,
            state=JobState.IDLE,
            url="",
        )
        children: List[UrlJobRequest] = []
        for p in self.contest.participants:
            url = p.url("health")
            self.log.debug(f"Creating child job for participant {p.id} with URL {url}")
            data = {"contest_id": self.contest.id}
            ur = UrlJobRequest(
                url=url,
                method="GET",
                channel=f"{channel}.{p.id}",
                data=json.dumps(data),
            )
            children.append(ur)

        batch = CommandJobBatchRequest(batch=batchJob, children=children)

        await self.message_broker.send_batch(batch)

    async def on_enter_setup_arena(self):
        """Called when entering the SetupArena state."""
        # Initialize the setup machine if it exists
        self.log.debug("Entering SetupArena state")
        setup_machine = self.setup_machine
        assert setup_machine is not None, "Setup machine should not be None"
        await setup_machine.activate_initial_state()  # type: ignore

    async def on_enter_in_round(self):
        """Called when entering the InRound state."""
        # Create a new round machine when entering the InRound state
        self._round_machine = RoundMachine(self.contest, log=self.log)

    def on_enter_checking_end(self):
        """Called when entering the CheckingEnd state."""

    def on_enter_completed(self):
        """Called when entering the Completed state."""

    @property
    def setup_machine(self) -> Optional[SetupMachine]:
        """
        Get the setup machine if in the InSetup state.

        Returns:
            Optional[SetupMachine]: The setup machine or None if not in InSetup state.
        """
        self.log.debug(f"getting setup_machine", state=self.current_state.id)
        if self.current_state.id != ContestState.SETUP_ARENA.value:
            return None
        if self._setup_machine is None:
            self.log.debug("Creating new SetupMachine instance")
            self._setup_machine = SetupMachine(
                self.contest,
                message_broker=self.message_broker,
                round_service=self.round_service,
                log=self.log,
            )
        return self._setup_machine

    @property
    def round_machine(self) -> Optional[RoundMachine]:
        """
        Get the round machine if in the InRound state.

        Returns:
            Optional[RoundMachine]: The round machine or None if not in InRound state.
        """
        if not self.current_state == self.in_round:
            return None
        return self._round_machine

    def check_setup_done(self) -> bool:
        """
        Check if setup is done.

        Returns:
            bool: True if setup is done, False otherwise.
        """
        if self._setup_machine is None:
            return False
        return (
            self._setup_machine.current_state.id
            == ContestRoundState.DESCRIBING_SETUP.value
        )

    def check_round_done(self) -> bool:
        """
        Check if round is done.

        Returns:
            bool: True if round is done, False otherwise.
        """
        if self._round_machine is None:
            return False
        return True

    def get_state_dict(self) -> Dict[str, Any]:
        """
        Get a dictionary representation of the current state.

        Returns:
            Dict[str, Any]: Dictionary with state information.
        """
        result = {
            "contest_state": self.current_state.id,
        }

        if self._setup_machine is not None:
            result["setup_state"] = self._setup_machine.current_state.id

        # if self.in_round.is_active and self._round_machine is not None:
        #     result["round_state"] = self._round_machine.current_state.id

        return result

    async def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")
        await self.message_broker.send_message(
            f"arena.contest.{self.contest.id}.contestflow.{source.id}.{target.id}",
            json.dumps(self.get_state_dict()),
        )

    def on_enter_state(self, target, event):
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
