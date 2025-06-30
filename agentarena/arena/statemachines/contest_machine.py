"""
The Contest State Machine
"""

import asyncio
import json
from codecs import decode
from datetime import datetime
from typing import Any
from typing import Dict
from typing import List

from nats.aio.msg import Msg
from statemachine import Event
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestRoundState
from agentarena.arena.models import ContestState
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import JudgeResult
from agentarena.arena.models import JudgeResultCreate
from agentarena.arena.models import Participant
from agentarena.arena.models import PlayerAction
from agentarena.arena.models import PlayerActionCreate
from agentarena.arena.models import PlayerState
from agentarena.arena.models import PlayerStateCreate
from agentarena.arena.services.round_service import RoundService
from agentarena.arena.services.view_service import ViewService
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.subscribing_service import Subscriber
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobBatchRequest
from agentarena.models.public import UrlJobRequest

from .round_machine import RoundMachine
from .setup_machine import SetupMachine


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
    create_round = State("create_round")
    in_round = State("in_round")
    check_end = State("check_end")
    fail = State("fail", final=True)
    complete = State("complete", final=True)

    # Transitions
    start_contest = starting.to(role_call)
    setup_done = setup_arena.to(in_round)
    setup_error = setup_arena.to(fail)
    round_created = create_round.to(in_round)
    round_complete = in_round.to(
        check_end, unless="current_round_failed"
    ) | in_round.to(fail)
    round_error = in_round.to(fail)
    contest_complete = check_end.to(complete)
    more_rounds = check_end.to(create_round)

    # Explicit Event definitions
    roles_present = Event(role_call.to(setup_arena))
    roles_error = Event(role_call.to(fail))

    def __init__(
        self,
        contest_id: str,
        message_broker: MessageBroker,
        feature_service: ModelService[Feature, FeatureCreate],
        judge_result_service: ModelService[JudgeResult, JudgeResultCreate],
        playeraction_service: ModelService[PlayerAction, PlayerActionCreate],
        player_state_service: ModelService[PlayerState, PlayerStateCreate],
        round_service: RoundService,
        uuid_service: UUIDService,
        view_service: ViewService,
        log: ILogger,
    ):
        """Initialize the contest machine."""
        self._setup_machine = None
        self._round_machine = None
        self.feature_service = feature_service
        self.message_broker = message_broker
        self.playeraction_service = playeraction_service
        self.player_state_service = player_state_service
        self.round_service = round_service
        self.uuid_service = uuid_service
        self.view_service = view_service
        self.judge_result_service = judge_result_service
        self.completion_channel = (
            f"arena.contest.{contest_id}.contestflow.setup.complete"
        )
        self.session = self.round_service.get_session()
        contest = self.session.get(Contest, contest_id)
        assert contest is not None, "Contest not found"
        self.contest = contest

        state = ContestState.STARTING.value
        if contest.rounds:
            round = contest.rounds[0]
            if round.state == ContestRoundState.SETUP_COMPLETE.value:
                state = ContestState.IN_ROUND.value
            elif round.state == ContestRoundState.SETUP_FAIL.value:
                # TODO: Maybe restart the setup machine?
                state = ContestState.FAIL.value
        self.subscriber = Subscriber()
        self.log = log.bind(contest_id=contest_id, state=state)
        StateMachine.__init__(self, start_value=state)
        self.log.info("setup complete")

    def current_round_failed(self) -> bool:
        """
        Check if the current round has failed.
        """
        if self._round_machine is None:
            return False
        return (
            self._round_machine.current_state.id == ContestRoundState.ROUND_FAIL.value
        )

    async def handle_role_call(self, msg: Msg):
        """
        Handle the role call message.

        This method is called when a role call message is received.
        It processes the message and transitions to the next state if needed.
        """
        self.log.info("Handling role call message", msg=msg)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        obj = None
        if not msg.data:
            self.log.error("Received empty role call message", msg=msg)
            return
        try:
            obj = json.loads(decode(msg.data, "utf-8", "unicode_escape"))
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
                asyncio.create_task(self.roles_present(job_id=job_id))  # type: ignore
            except Exception as e:
                self.log.error(
                    "Failed to transition from role_call to setup_arena",
                    error=str(e),
                    exc_info=True,
                    job_id=job_id,
                    contest_id=self.contest.id,
                    current_state=self.current_state.id,
                )
                self.roles_error(job_id=job_id, error_type=type(e).__name__)
        elif job_state == JobState.FAIL.value:
            self.log.error("Role call failed, transitioning to fail state")
            self.roles_error(job_id=job_id, error_type="JobFailed")
        else:
            self.log.warn(
                f"Role call message in unexpected state: {job_state}, ignoring message"
            )
            # Optionally, you could handle other states or log them
            return

    async def handle_round_complete(self, msg: Msg):
        """Handle the round complete message."""
        self.log.info("Handling round complete message", msg=msg)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        asyncio.create_task(self.round_complete(""))  # type: ignore

    async def handle_setup_complete(self, msg: Msg):
        """Handle the setup complete message."""
        self.log.info("Handling setup complete message", msg=msg)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        final_state = decode(msg.data, "utf-8", "unicode_escape")
        if final_state == ContestRoundState.SETUP_COMPLETE.value:
            self.log.info("Setup complete, transitioning to in_round")
            asyncio.create_task(self.setup_done(""))  # type: ignore
        elif final_state == ContestRoundState.SETUP_FAIL.value:
            self.log.warn(f"Setup machine in fail state: {final_state}")
            asyncio.create_task(self.setup_error(""))  # type: ignore
        else:
            self.log.warn(f"Setup machine in unexpected state: {final_state}")
            asyncio.create_task(self.setup_error(""))  # type: ignore

    async def on_enter_role_call(self):
        """Called when entering the InSetup state."""
        job_id = self.uuid_service.make_id()
        channel = f"arena.contest.{self.contest.id}.role_call"
        await self.subscriber.subscribe(
            self.message_broker.client, channel, self.log, cb=self.handle_role_call
        )

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
        # Access job_id via event_data.kwargs.get("job_id") if needed
        self.log.info("Entering SetupArena state")
        if self._setup_machine is None:
            self.log.debug("Creating new SetupMachine instance")
            self._setup_machine = SetupMachine(
                self.contest,
                feature_service=self.feature_service,
                message_broker=self.message_broker,
                round_service=self.round_service,
                view_service=self.view_service,
                session=self.session,
                log=self.log,
            )

        setup_machine = self._setup_machine
        assert (
            setup_machine is not None
        ), "Setup machine should not be None during on_enter_setup_arena"
        channel = setup_machine.completion_channel
        await self.subscriber.subscribe(
            self.message_broker.client, channel, self.log, cb=self.handle_setup_complete
        )
        await setup_machine.activate_initial_state()  # type: ignore
        await setup_machine.start_generating_features("from contest machine")

    async def on_enter_create_round(self):
        """Called when entering the CreateRound state, which happens for all rounds after the first."""
        self.log.info("Entering CreateRound state")
        rc = ContestRoundCreate(
            contest_id=self.contest.id,
            round_no=len(self.contest.rounds),
            narrative=self.contest.rounds[-1].ending_narrative or "",
            ending_narrative=None,
            state=ContestRoundState.IDLE,
        )
        created, result = await self.round_service.create(rc, self.session)
        if not created or not result.success:
            self.log.error("Failed to create round", error=result)
            asyncio.create_task(self.round_error(""))  # type: ignore
            return
        self.log.info("Round created", round=created.id)
        self.contest.current_round = len(self.contest.rounds)
        self.contest.rounds.append(created)
        self.session.commit()
        asyncio.create_task(self.round_created(""))  # type: ignore

    async def on_enter_in_round(self):
        """Called when entering the InRound state.
        This will create a new round machine and subscribe to the round complete channel.
        When it is complete, it will send a message to the contest machine to transition to the next state.
        """
        # Create a new round machine when entering the InRound state
        round = self.contest.rounds[-1]
        round.state = ContestRoundState.IN_PROGRESS
        self.session.commit()
        self._round_machine = RoundMachine(
            round,
            feature_service=self.feature_service,
            judge_result_service=self.judge_result_service,
            message_broker=self.message_broker,
            player_action_service=self.playeraction_service,
            player_state_service=self.player_state_service,
            session=self.session,
            view_service=self.view_service,
            log=self.log,
        )
        channel = self._round_machine.completion_channel
        await self.subscriber.subscribe(
            self.message_broker.client, channel, self.log, cb=self.handle_round_complete
        )
        await self._round_machine.activate_initial_state()  # type: ignore

    def on_enter_check_end(self):
        """Called when entering the CheckEnd state."""
        # We could check using an LLM, but for now we'll just check the scores
        round = self.contest.rounds[-1]
        for state in round.player_states:
            if state.score > 100:
                self.log.info("Player has won", player=state.participant.name)
                asyncio.create_task(self.contest_complete(state.participant))  # type: ignore
                return
        self.log.info("No player has won, continuing to next round")
        asyncio.create_task(self.more_rounds(""))  # type: ignore

    def on_enter_complete(self, winner: Participant):
        """Called when entering the Complete state."""
        self.log.info("Contest complete")
        self.contest.winner_id = winner.id
        self.contest.updated_at = int(datetime.now().timestamp())
        self.session.commit()
        asyncio.create_task(self.subscriber.unsubscribe_all(self.log))

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
        return result

    async def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")
        await self.message_broker.send_message(
            f"arena.contest.{self.contest.id}.contestflow.{source.id}.{target.id}",
            json.dumps(self.get_state_dict()),
        )

    async def on_enter_state(self, target, event):
        self.contest.state = target.id
        self.contest.updated_at = int(datetime.now().timestamp())
        self.session.commit()

        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
            await self.subscriber.unsubscribe_all(self.log)
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
