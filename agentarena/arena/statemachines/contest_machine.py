"""
The Contest State Machine
"""

import asyncio
from codecs import decode
from datetime import datetime
from typing import Any
from typing import Dict

from nats.aio.msg import Msg
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

    cycle = (
        starting.to(role_call)
        | role_call.to(setup_arena)
        | create_round.to(in_round)
        | in_round.to(check_end, unless="current_round_failed")
        | in_round.to(fail, cond="current_round_failed")
        | check_end.to(complete, cond="has_winner")
        | check_end.to(create_round, unless="has_winner")
    )

    setup_complete = setup_arena.to(in_round)

    round_complete = in_round.to(check_end)

    # Explicit Event definitions
    step_failed = (
        role_call.to(fail)
        | setup_arena.to(fail)
        | in_round.to(fail)
        | check_end.to(fail)
    )

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
        self.completion_channel = f"arena.contest.{contest_id}.contestmachine.complete"
        self.session = self.round_service.get_session()
        contest = self.session.get(Contest, contest_id)
        assert contest is not None, "Contest not found"
        self.contest = contest

        state = ContestState.STARTING.value
        if contest.rounds:
            round = contest.rounds[-1]
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
            if self.contest.rounds:
                round = self.contest.rounds[-1]
                if round.state == ContestRoundState.SETUP_FAIL.value:
                    return True
            return False
        return (
            self._round_machine.current_state.id == ContestRoundState.ROUND_FAIL.value
        )

    def has_winner(self) -> bool:
        """
        Check if the contest has a winner.
        """
        return self.contest.winner_id is not None

    async def on_enter_role_call(self):
        """Called when entering the InSetup state."""
        self.log.info("starting role call")
        healthy = True
        missing = []
        for p in self.contest.participants:
            log = self.log.bind(participant=p.name, role=p.role)
            job_id = self.uuid_service.make_id()
            channel = p.channel(f"request.health.{job_id}")
            log.info("requesting health from participant", channel=channel)
            msg: Msg = await self.message_broker.request_job(channel, self.contest.id)
            if msg.data:
                log.info("Participant is healthy")
            else:
                missing.append(p.name)
                log.error("Participant is not healthy")
                healthy = False
        if healthy:
            await self.cycle("roles present")  # type: ignore
        else:
            await self.roles_error("failed to get", missing=missing)  # type: ignore

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
            await self.step_failed("round creation failed")  # type: ignore
            return
        self.log.info("Round created", round=created.id)
        self.contest.current_round = len(self.contest.rounds) - 1
        self.contest.rounds.append(created)
        self.session.commit()
        await self.cycle("round created")  # type: ignore

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

    async def on_enter_check_end(self):
        """Called when entering the CheckEnd state."""
        # We could check using an LLM, but for now we'll just check the scores
        round = self.contest.rounds[-1]
        has_winner = False
        for state in round.player_states:
            if state.score > 100:
                self.log.info("Player has won", player=state.participant.name)
                self.contest.winner_id = state.participant.id
                self.contest.updated_at = int(datetime.now().timestamp())
                self.session.commit()
                has_winner = True
        else:
            self.log.info("No player has won, continuing to next round")
        await self.cycle("winner found" if has_winner else "no winner found")  # type: ignore

    async def on_enter_complete(self, winner: Participant):
        """Called when entering the Complete state."""
        self.log.info("Contest complete")
        await self.subscriber.unsubscribe_all(self.log)

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
        if self._round_machine is not None:
            result["round_state"] = self._round_machine.current_state.id
        return result

    # async def after_transition(self, event, source, target):
    #     self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")
    #     await self.message_broker.send_message(
    #         f"arena.contest.{self.contest.id}.contestmachine.{source.id}.{target.id}",
    #         json.dumps(self.get_state_dict()),
    #     )

    async def on_enter_state(self, target, event):
        self.contest.state = target.id
        self.contest.updated_at = int(datetime.now().timestamp())
        self.session.commit()

        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
            await self.subscriber.unsubscribe_all(self.log)
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")

    # message handlers

    async def handle_round_complete(self, msg: Msg):
        """Handle the round complete message."""
        state = decode(msg.data, "utf-8", "unicode_escape")
        self.log.info("Handling round complete message", msg=msg.subject, state=state)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        task = (
            self.round_complete
            if state == ContestRoundState.ROUND_COMPLETE.value
            else self.step_failed
        )
        asyncio.create_task(task("from round machine completion message"))  # type: ignore

    async def handle_setup_complete(self, msg: Msg):
        """Handle the setup complete message."""
        state = decode(msg.data, "utf-8", "unicode_escape")
        self.log.info("Handling setup complete message", msg=msg.subject, state=state)
        await self.subscriber.unsubscribe(msg.subject, self.log)
        task = (
            self.setup_complete
            if state == ContestRoundState.SETUP_COMPLETE.value
            else self.step_failed
        )
        asyncio.create_task(task("from setup machine completion message"))  # type: ignore
