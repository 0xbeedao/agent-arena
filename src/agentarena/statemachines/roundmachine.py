from pydantic import Field
from statemachine import State
from statemachine import StateMachine

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.contest import Contest


class RoundMachine(StateMachine):
    """
    Round machine for handling the flow of a single round.

    States:
    - RoundPrompting: Initial state for prompting
    - AwaitingActions: State for awaiting actions
    - JudgingActions: State for judging actions
    - ApplyingEffects: State for applying effects
    - DescribingResults: State for describing results
    - PresentingResults: State for presenting results
    """

    round_prompting = State("RoundPrompting", initial=True)
    awaiting_actions = State("AwaitingActions")
    judging_actions = State("JudgingActions")
    applying_effects = State("ApplyingEffects")
    describing_results = State("DescribingResults")
    presenting_results = State("PresentingResults", final=True)

    # cycle = (
    #     round_prompting.to(awaiting_actions)
    #     | awaiting_actions.to(judging_actions)
    #     | judging_actions.to(applying_effects)
    #     | applying_effects.to(describing_results)
    #     | presenting_results.to(complete)
    # )

    # Transitions
    prompt_sent = round_prompting.to(awaiting_actions)
    actions_received = awaiting_actions.to(judging_actions)
    raw_results = judging_actions.to(applying_effects)
    effects_determined = applying_effects.to(describing_results)
    results_ready = describing_results.to(presenting_results)

    def __init__(
        self,
        contest: Contest,
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """Initialize the round machine."""
        self.contest = contest
        self.log = logging.get_logger(
            "machine", contest=contest.id if contest else "none"
        )
        super().__init__()

    def on_enter_round_prompting(self):
        """Called when entering the RoundPrompting state."""

    def on_enter_awaiting_actions(self):
        """Called when entering the AwaitingActions state."""

    def on_enter_judging_actions(self):
        """Called when entering the JudgingActions state."""

    def on_enter_applying_effects(self):
        """Called when entering the ApplyingEffects state."""

    def on_enter_describing_results(self):
        """Called when entering the DescribingResults state."""

    def on_enter_presenting_results(self):
        """Called when entering the PresentingResults state."""

    # logging changes
    def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target, event):
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
