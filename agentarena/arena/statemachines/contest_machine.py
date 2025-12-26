"""
The Contest State Machine
"""

from datetime import datetime
from typing import Any
from typing import Dict

from nats.aio.msg import Msg
from sqlmodel import Session
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
        | setup_arena.to(
            create_round,
            unless="current_round_failed",
            cond="no_opening_round",
        )
        | setup_arena.to(
            in_round,
            unless="current_round_failed",
            cond="has_opening_round",
        )
        | setup_arena.to(fail, cond="current_round_failed")
        | create_round.to(in_round)
        | in_round.to(check_end, unless="current_round_failed")
        | in_round.to(fail, cond="current_round_failed")
        | check_end.to(complete, cond="has_winner")
        | check_end.to(create_round, unless="has_winner")
    )

    # Explicit Event definitions
    step_failed = (
        role_call.to(fail)
        | setup_arena.to(fail)
        | in_round.to(fail)
        | check_end.to(fail)
    )

    def __init__(
        self,
        contest: Contest,
        message_broker: MessageBroker,
        feature_service: ModelService[Feature, FeatureCreate],
        judge_result_service: ModelService[JudgeResult, JudgeResultCreate],
        playeraction_service: ModelService[PlayerAction, PlayerActionCreate],
        player_state_service: ModelService[PlayerState, PlayerStateCreate],
        round_service: RoundService,
        session: Session,
        uuid_service: UUIDService,
        view_service: ViewService,
        log: ILogger,
        auto_advance: bool = True,
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
        self.session = session
        assert contest is not None, "Contest required"
        self.contest = contest
        self.auto_advance = auto_advance

        state = contest.state.value or ContestState.STARTING.value
        if state == ContestState.CREATED.value:
            state = ContestState.STARTING.value
        self.log = log.bind(contest=contest.id, state=state)
        StateMachine.__init__(self, start_value=state)
        self.log.info("contest machine initialized")

    def current_round_failed(self) -> bool:
        """
        Check if the current round has failed.
        """
        if self._round_machine is not None:
            return (
                self._round_machine.current_state.id
                == ContestRoundState.ROUND_FAIL.value
            )

        if self._setup_machine is not None:
            return (
                self._setup_machine.current_state.id
                == ContestRoundState.SETUP_FAIL.value
            )

        if self.contest.rounds:
            round = self.contest.rounds[-1]
            return round.state in [
                ContestRoundState.SETUP_FAIL.value,
                ContestRoundState.ROUND_FAIL.value,
            ]

        if self.contest.state == ContestState.FAIL.value:
            return True

        return False

    def has_opening_round(self) -> bool:
        """
        Check if the contest has an opening round.
        """
        return len(self.contest.rounds) > 0

    def no_opening_round(self) -> bool:
        """
        Check if the contest has no opening round.
        """
        return len(self.contest.rounds) == 0

    def has_round_machine(self) -> bool:
        """
        Check if the contest has a round machine.
        """
        return self._round_machine is not None

    def has_setup_machine(self) -> bool:
        """
        Check if the contest has a setup machine.
        """
        return self._setup_machine is not None

    def has_winner(self) -> bool:
        """
        Check if the contest has a winner.
        """
        return self.contest.winner_id is not None

    async def cycle_or_pause(self, label: str, target_state: str = ""):
        """
        Cycle the contest machine, either advancing to the next state or
        pausing.

        On a pause, the machine will update the contest state to the target
        state, if needed, and send a message that the contest machine is
        paused.
        """
        if self.auto_advance:
            await self.advance_state(label)
        else:
            current_state = self.current_state_value or "ERROR - NO STATE"
            if target_state and target_state != current_state:
                self.log.info(
                    "Updating contest state",
                    target_state=target_state,
                )
                self.contest.state = target_state
                self.contest.updated_at = int(datetime.now().timestamp())
                self.session.commit()
            self.log.debug(
                "Pausing state machine",
                target_state=target_state or "no target state",
                source_state=current_state,
            )
            await self.message_broker.send_message(
                f"arena.contest.{self.contest.id}.contestmachine.{self.current_state_value.lower()}.pause",
                target_state,
            )

    async def advance_state(self, event: str):
        log = self.log.bind(event=event)
        round_machine = self._round_machine
        setup_machine = self._setup_machine
        if (
            round_machine is not None
            and round_machine.current_state_value not in [
                ContestRoundState.ROUND_COMPLETE.value,
                ContestRoundState.ROUND_FAIL.value,
            ]

        ):
            log.debug("cycling round machine")
            await round_machine.cycle(event)
            if round_machine.current_state_value == ContestRoundState.COMPLETE.value:
                await self.cycle_or_pause("round complete", "check_end")  # type: ignore
            elif round_machine.current_state_value == ContestRoundState.FAIL.value:
                await self.step_failed("round failed")  # type: ignore
        elif (
            setup_machine is not None
            and setup_machine.current_state_value not in [
                ContestRoundState.SETUP_COMPLETE.value,
                ContestRoundState.SETUP_FAIL.value,
            ]
        ):
            log.debug("cycling setup machine")
            await setup_machine.cycle(event)  # type: ignore
            if setup_machine.current_state_value == ContestRoundState.SETUP_COMPLETE.value:
                await self.cycle_or_pause("setup complete", "in_round")  # type: ignore
            elif setup_machine.current_state_value == ContestRoundState.SETUP_FAIL.value:
                await self.step_failed("setup failed")
        else:
            log.debug("cycling contest machine")
            await self.cycle(event)

    async def on_enter_role_call(self):
        """Called when entering the role call state."""
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
            await self.cycle_or_pause("roles present", "setup_arena")  # type: ignore
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
                auto_advance=self.auto_advance,
            )

        setup_machine = self._setup_machine

        await setup_machine.activate_initial_state()  # type: ignore
        if setup_machine.current_state in [
            ContestRoundState.SETUP_COMPLETE.value,
            ContestRoundState.SETUP_FAIL.value,
        ]:
            await self.cycle_or_pause("setup complete", "create_round")  # type: ignore

    async def on_enter_create_round(self):
        """Called when entering the CreateRound state, which happens for all
        rounds after the first."""
        self.log.info("Entering CreateRound state")
        narrative = ""
        needs_round = True
        if self.contest.rounds:
            narrative = self.contest.rounds[-1].ending_narrative or ""
            current_round = self.contest.rounds[-1]
            if current_round.state == ContestRoundState.IDLE.value:
                self.log.info("Not creating new, round, current is IDLE")
                needs_round = False
        if needs_round:
            rc = ContestRoundCreate(
                contest_id=self.contest.id,
                round_no=len(self.contest.rounds),
                narrative=narrative,
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
        await self.cycle_or_pause("created round", "in_round")  # type: ignore

    async def on_enter_in_round(self):
        """Called when entering the InRound state.
        This will create a new round machine and subscribe to the
        round complete channel. When it is complete, it will send
        a message to the contest machine to transition to the next state.
        """
        # Create a new round machine when entering the InRound state
        if self._setup_machine is not None:
            self._setup_machine = None
            self.log.info("Setup machine destroyed")

        current_round = self.contest.rounds[-1]
        if current_round.state in [
            ContestRoundState.IDLE.value,
            ContestRoundState.SETUP_COMPLETE.value,
        ]:
            self.log.info("Starting round", round=current_round.id)
            current_round.state = ContestRoundState.ROUND_PROMPTING
            self.session.commit()
        self._round_machine = RoundMachine(
            current_round,
            feature_service=self.feature_service,
            judge_result_service=self.judge_result_service,
            message_broker=self.message_broker,
            player_action_service=self.playeraction_service,
            player_state_service=self.player_state_service,
            session=self.session,
            view_service=self.view_service,
            log=self.log,
            auto_advance=self.auto_advance,
        )
        await self._round_machine.activate_initial_state()  # type: ignore
        if self._round_machine.current_state == ContestRoundState.COMPLETE.value:
            await self.cycle_or_pause("round complete", "check_end")  # type: ignore
        elif self._round_machine.current_state == ContestRoundState.FAIL.value:
            await self.step_failed("round failed")  # type: ignore

    async def on_enter_check_end(self):
        """Called when entering the CheckEnd state."""
        # We could check using an LLM, but for now we'll just check the scores
        if self._round_machine is not None:
            self._round_machine = None
            self.log.info("Round machine destroyed")

        current_round = self.contest.rounds[-1]
        has_winner = False
        for state in current_round.player_states:
            if state.score > 100:
                self.log.info("Player has won", player=state.participant.name)
                self.contest.winner_id = state.participant.id
                self.contest.updated_at = int(datetime.now().timestamp())
                self.session.commit()
                has_winner = True
        if not has_winner:
            self.log.info("No player has won, continuing to next round")
        if self.has_winner():
            label = "winner found"
            next_state = "complete"
        else:
            label = "no winner found"
            next_state = "create_round"
        await self.cycle_or_pause(label, next_state)  # type: ignore

    async def on_enter_complete(self, winner: Participant):
        """Called when entering the Complete state."""
        self.log.info("Contest complete", winner=winner)

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
        log = self.log.bind(state=target.id)
        log.debug("entering state")
        self.contest.state = target.id
        self.contest.updated_at = int(datetime.now().timestamp())
        self.session.commit()

        if target.final:
            log.debug(f"{self.name} enter final state: {target.id} from {event}")
            await self.subscriber.unsubscribe_all(self.log)
        else:
            log.debug(f"{self.name} enter: {target.id} from {event}")
