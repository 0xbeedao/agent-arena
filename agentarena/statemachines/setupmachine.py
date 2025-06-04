import json
import secrets

from nats.aio.msg import Msg
from sqlmodel import Field
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestRoundState
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService
from agentarena.models.constants import PromptType, RoleType
from agentarena.models.job import CommandJob
from agentarena.models.requests import ParticipantRequest


class SetupMachine(StateMachine):
    """
    Setup machine for generating features, positions, and descriptions.

    States:
    - GeneratingFeatures: Initial state for generating features
    - GeneratingPositions: State for generating positions
    - DescribingSetup: State for describing the setup
    """

    idle = State(ContestRoundState.IDLE.value, initial=True)
    creating_round = State(ContestRoundState.CREATING_ROUND.value)
    adding_fixed_features = State(ContestRoundState.ADDING_FIXED_FEATURES.value)
    generating_features = State(ContestRoundState.GENERATING_FEATURES.value)
    generating_positions = State(ContestRoundState.GENERATING_POSITIONS.value)
    describing_setup = State(ContestRoundState.DESCRIBING_SETUP.value)
    complete = State(ContestRoundState.COMPLETE.value, final=True)
    fail = State(ContestRoundState.FAIL.value, final=True)

    # Transitions
    start_generating_features = idle.to(
        creating_round,
        unless="has_opening_round",
    ) | idle.to(
        adding_fixed_features,
        cond="has_opening_round",
    )

    step_failed = (
        creating_round.to(fail)
        | adding_fixed_features.to(fail)
        | generating_features.to(fail)
        | generating_positions.to(fail)
        | describing_setup.to(fail)
    )

    cycle = (
        creating_round.to(adding_fixed_features)
        | adding_fixed_features.to(generating_features)
        | generating_features.to(generating_positions)
        | generating_positions.to(describing_setup)
        | describing_setup.to(complete)
    )

    def __init__(
        self,
        contest: Contest,
        message_broker: MessageBroker = Field(description="Message Broker"),
        round_service: ModelService[ContestRound, ContestRoundCreate] = Field(
            description="Round Service"
        ),
        log: ILogger = Field(description="Log"),
    ):
        """Initialize the setup machine."""
        self.contest = contest
        self.contest_round: ContestRound | None = None
        self.message_broker = message_broker
        self.round_service = round_service
        self.log = log.bind(contest_id=contest.id)
        self.subscriptions = {}
        if contest.rounds:
            self.contest_round = contest.rounds[0]
        super().__init__()

    async def generate_random_features(self, count: int):
        """Generate a list of random features up to count, by sending jobs to the message broker,
        which will come back on our handler."""
        actual = secrets.randbelow(count) + 1
        log = self.log.bind(state="generating_random_features", count=actual)
        log.debug("generating")
        agents = self.contest.get_role(RoleType.ARENA)
        if not agents:
            log.error("No arena agents found for generating features")
            return
        arena_agent = agents[0]
        log = log.bind(arena_agent=arena_agent.name)
        log.info("requesting random features from arena agent")
        channel = f"arena.contest.{self.contest.id}.setup.features"
        job_id = self.uuid_service.make_id()
        contest = self.contest.get_public()
        req = ParticipantRequest(
            job_id=job_id,
            command=PromptType.ARENA_GENERATE_FEATURES,
            data=contest.model_dump_json(),
            message="",
        )

        job = CommandJob(
            channel=channel,
            data=req.model_dump_json(),
            method="POST",
            url=arena_agent.url("request"),
        )
        await self.message_broker.send_job(job)
        sub = self.message_broker.client.subscribe(
            channel, cb=self.handle_feature_generation_message
        )
        self.subscriptions[channel] = sub

    async def handle_feature_generation_message(self, msg: Msg):
        """Handle the message from the arena agent with generated features."""
        log = self.log.bind(msg=msg.subject)
        log.debug("Received feature generation message", msg=msg)
        try:
            features_data = msg.data.decode("utf-8")
            # TODO - finish
            log.info("Parsed feature generation message", data=features_data)
            await self.subscriptions[msg.subject].unsubscribe()
            # await self.cycle("from feature generation message")
        except Exception as e:
            log.error("Failed to parse feature generation message", error=e)
            await self.failed("bad feature generation message")

    def has_opening_round(self) -> bool:
        """Check if the contest has an opening round."""
        return self.contest_round is not None and self.contest_round.round_no == 0

    async def on_enter_creating_round(self):
        """Called when entering the CreatingRound state."""
        log = self.log.bind(state="creating_round")
        log.info("Creating round 0 for contest")

        # Create a new round 0 if it doesn't exist
        if not self.contest_round:
            round = ContestRound(
                id=self.contest.id,
                round_no=0,
                contest_id=self.contest.id,
                state=ContestRoundState.IDLE,
            )
            with self.round_service.get_session() as session:
                round, response = await self.round_service.create(round, session)
                if not response.success:
                    log.error("Failed to create round 0", response=response)
                    return
                if not round:
                    log.error("Failed to create round 0, no round returned")
                    return
                session.commit()
                self.contest_round = round
                self.log = self.log.bind(round_id=round.id)
                log.info("Round 0 created successfully", round_id=round.id)

        await self.cycle("from creating round")

    async def on_enter_adding_fixed_features(self):
        """Called when entering the AddingFixedFeatures state."""
        log = self.log.bind(state="adding_fixed_features")
        log.info("Adding fixed features to round 0")
        round = self.contest_round

        # Ensure we have a contest round
        if not round:
            log.error("INVALID STATE! No contest round available, cannot add features")
            return

        ct = 0
        with self.round_service.get_session() as session:
            session.add(round)
            log.info("Copying arena features to round 0")
            for feature in self.contest.arena.features:
                log.debug(f"Adding feature", feature=feature.name)
                round.features.append(feature)
                ct += 1

            session.commit()

        log.info(f"{ct} Fixed features added successfully")
        await self.cycle("from adding fixed features")

    async def on_enter_generating_features(self):
        """Called when entering the GeneratingFeatures state, which adds the random features."""
        log = self.log.bind(state="generating_features")
        round = self.contest_round
        # Ensure we have a contest round
        if not round:
            log.error("INVALID STATE! No contest round available, cannot add features")
            return

        if self.contest.arena.max_random_features <= 0:
            log.info("No random features to generate, skipping")
            await self.cycle("from generating features")
            return
        # Generate random features and add them to the round
        log.info("Starting")
        ct = 0
        await self.generate_random_features(self.contest.arena.max_random_features)

    def on_enter_generating_positions(self):
        """Called when entering the GeneratingPositions state."""

    def on_enter_describing_setup(self):
        """Called when entering the DescribingSetup state."""

    async def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")
        await self.message_broker.send_message(
            f"arena.contest.{self.contest.id}.constestflow.setup.{source.id}.{target.id}",
            json.dumps(self.get_state_dict()),
        )

    def on_enter_state(self, target, event):
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
