from sqlmodel import Field
from statemachine import State
from statemachine import StateMachine

from agentarena.arena.models import Contest
from agentarena.core.factories.logger_factory import LoggingService


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
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """Initialize the setup machine."""
        self.contest = contest
        self.log = logging.get_logger(
            "machine", contest=contest.id if contest else "none"
        )
        super().__init__()

    def on_enter_generating_features(self):
        """Called when entering the GeneratingFeatures state."""
        self.log.info("state generating_features")

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
