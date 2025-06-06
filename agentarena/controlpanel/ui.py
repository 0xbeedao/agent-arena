"""Control Panel UI using Textual."""

from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Button
from textual.widgets import Collapsible
from textual.widgets import ContentSwitcher
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Label
from textual.widgets import Static

from agentarena.controlpanel.contest_view import ContestView
from agentarena.controlpanel.dashboard_view import DashboardView
from agentarena.core.factories.logger_factory import ILogger


class StatusBar(Static):
    """Status bar at bottom of screen."""

    def compose(self) -> ComposeResult:
        yield Label("Ready", id="status-message")
        yield Label("", id="status-controls")


class ControlPanelUI(App):
    """Main UI application."""

    CSS_PATH = "controlpanel.css"

    def __init__(self, clients, logger):
        super().__init__()
        self.loggingservice = logger
        self._structlog: ILogger = logger.get_logger("ui")
        self.clients = clients

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal(id="buttons"):
            yield Button("Dashboard", id="dashboard")
            yield Button("Job Visualizer", id="jobviz")
            yield Button("Contest", id="contest")
        with ContentSwitcher(initial="dashboard"):
            with Vertical(id="dashboard"):
                yield DashboardView(self.clients, self.loggingservice)
            with Vertical(id="jobviz"):
                yield Label("Job Visualizer Content")
            with Vertical(id="contest"):
                yield ContestView(self.clients, self.loggingservice)
        yield StatusBar()
        yield Footer()

    def setup(self) -> None:
        """Setup the UI components."""

    def main_loop(self) -> None:
        """Run the main UI loop."""
        self.run()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self._structlog.info("button", btn=event.button.id)
        self.query_one(ContentSwitcher).current = event.button.id

    async def on_collapsible_expanded(self, event: Collapsible.Expanded) -> None:
        self._structlog.info("collapsible", trigger=event.collapsible.id)
        await self.query_one(DashboardView).on_collapsible_expanded(event)

    async def show_contest(self, contest_obj):
        # Switch to contest view
        self.query_one(ContentSwitcher).current = "contest"
        # Update the ContestView's contest attribute
        contest_view = self.query_one(ContestView)
        contest_view.contest = contest_obj
        contest_view.refresh()
