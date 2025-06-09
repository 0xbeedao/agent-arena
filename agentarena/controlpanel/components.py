from textual.widgets import Label

from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import ContestState
from agentarena.models.constants import JobResponseState


class StatusLabel(Label):
    """A label for displaying job response status with color and bold styling."""

    STATE_STYLES = {
        JobResponseState.COMPLETE: "green",
        JobResponseState.PENDING: "yellow",
        JobResponseState.FAIL: "red",
        ContestState.CREATED: "green",
        ContestState.COMPLETE: "green",
        ContestState.FAIL: "red",
        ContestState.STARTING: "yellow",
        ContestState.ROLE_CALL: "yellow",
        ContestState.SETUP_ARENA: "yellow",
        ContestState.IN_ROUND: "yellow",
        ContestState.CHECK_WIN: "yellow",
        ContestRoundState.IDLE: "green",
        ContestRoundState.CREATING_ROUND: "yellow",
        ContestRoundState.ADDING_FIXED_FEATURES: "yellow",
        ContestRoundState.GENERATING_FEATURES: "yellow",
        ContestRoundState.DESCRIBING_SETUP: "yellow",
        ContestRoundState.SETUP_COMPLETE: "green",
        ContestRoundState.SETUP_FAIL: "red",
        ContestRoundState.IN_PROGRESS: "yellow",
        ContestRoundState.COMPLETE: "green",
        ContestRoundState.FAIL: "red",
        ContestRoundState.ROUND_PROMPTING: "yellow",
        ContestRoundState.AWAITING_ACTIONS: "yellow",
        ContestRoundState.JUDGING_ACTIONS: "yellow",
        ContestRoundState.APPLYING_EFFECTS: "yellow",
        ContestRoundState.DESCRIBING_RESULTS: "yellow",
        ContestRoundState.PRESENTING_RESULTS: "yellow",
        ContestRoundState.ROUND_COMPLETE: "green",
        ContestRoundState.ROUND_FAIL: "red",
    }

    def __init__(self, state: JobResponseState, **kwargs):
        super().__init__(str(state).capitalize(), **kwargs)
        self.update_state(state)

    def update_state(self, state: JobResponseState):
        self.state = state
        markup = (
            f"[bold][{self.STATE_STYLES[state]}]{str(state).capitalize()}[/][/bold]"
        )

        self.update(markup)
