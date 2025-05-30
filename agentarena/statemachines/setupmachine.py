import secrets
from typing import List

from sqlmodel import Field
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundCreate
from agentarena.arena.models import ContestRoundState
from agentarena.arena.models import Feature
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.services.model_service import ModelService


class SetupMachine(StateMachine):
    """
    Setup machine for generating features, positions, and descriptions.

    States:
    - GeneratingFeatures: Initial state for generating features
    - GeneratingPositions: State for generating positions
    - DescribingSetup: State for describing the setup
    """

    generating_features = State("GeneratingFeatures", initial=True)
    generating_positions = State("GeneratingPositions")
    describing_setup = State("DescribingSetup", final=True)

    # Transitions
    features_generated = generating_features.to(generating_positions)
    positions_generated = generating_positions.to(describing_setup)

    cycle = generating_features.to(generating_positions) | generating_positions.to(
        describing_setup
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
        self._contest_round: ContestRound | None = None
        self.message_broker = message_broker
        self.round_service = round_service
        self.log = log
        if contest.rounds:
            self._contest_round = contest.rounds[0]
        super().__init__()

    async def generate_features(self):
        """Generate features for the contest."""
        assert (
            self._contest_round
        ), "Contest round must be set before generating features"
        log = self.log.bind(state="generating_features", contest=self.contest.id)
        log.info("Generating features for contest", contest_id=self.contest.id)

        with self.model_service.session() as session:
            round = self._contest_round
            session.add(round)
            log.info("Copying arena features to round 0")
            for feature in self.contest.arena.features:
                log.debug(f"Adding feature {feature.name} to round 0")
                round.features.append(feature)

            if self.contest.arena.max_random_features > 0:
                log.info(
                    f"Adding up to {self.contest.arena.max_random_features} random features to round 0"
                )
                features = await self.generate_random_features(
                    self.contest.arena.max_random_features
                )
                for feature in features:
                    round.features.append(feature)
            session.commit()

        log.info("Features generated successfully")

    async def generate_random_features(self, count: int) -> List[Feature]:
        """Generate a list of random features up to count."""
        actual = secrets.randbelow(count) + 1
        log = self.log.bind(
            state="generating_features", count=actual, contest=self.contest.id
        )
        log.info(f"Generating {actual} random features")
        # This is a placeholder for actual feature generation logic
        # In a real implementation, this would generate meaningful features
        return []

    async def on_enter_generating_features(self):
        """Called when entering the GeneratingFeatures state."""
        log = self.log.bind(state="generating_features", contest=self.contest.id)
        log.info("starting")
        # We need to generate features for the contest, these will be added to
        # the ContestRound for round 0.

        # first, do we have an existing round 0?
        if not self._contest_round:
            log.info("No existing round 0, creating new one")
            # Create a new round 0 if it doesn't exist
            round = ContestRound(
                id=self.contest.id,
                round_no=0,
                contest_id=self.contest.id,
                state=ContestRoundState.GENERATING_FEATURES,
            )
            with self.model_service.session() as session:
                round, response = await self.round_service.create(round, session)
                if not response.success:
                    log.error("Failed to create round 0", response=response)
                    return
                if not round:
                    log.error("Failed to create round 0, no round returned")
                    return
                session.commit()
                self._contest_round = round

        await self.generate_features()

    def on_enter_generating_positions(self):
        """Called when entering the GeneratingPositions state."""

    def on_enter_describing_setup(self):
        """Called when entering the DescribingSetup state."""

    # logging changes
    def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target, event):
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
