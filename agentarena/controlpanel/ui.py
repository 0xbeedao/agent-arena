"""Control Panel UI using Textual."""

from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button
from textual.widgets import Collapsible
from textual.widgets import ContentSwitcher
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Label
from textual.widgets import Static
from textual.binding import Binding

from agentarena.controlpanel.contest_view import ContestView
from agentarena.controlpanel.dashboard_view import DashboardView
from agentarena.core.factories.logger_factory import ILogger


class StatusBar(Static):
    """Status bar at bottom of screen."""

    def compose(self) -> ComposeResult:
        yield Label("Ready", id="status-message")
        yield Label("", id="status-controls")


def decorated_tab(label: str, tab_id: str, current_tab: str | None):
    if current_tab == tab_id:
        return f"[bold]{label}[/bold]"
    else:
        return tab_id


class ControlPanelUI(App):
    """Main UI application."""

    CSS_PATH = "controlpanel.css"
    current_tab = reactive("dashboard")

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("^", "next_tab", "Next Tab"),
    ]

    def __init__(self, clients, logger):
        super().__init__()
        self.loggingservice = logger
        self._structlog: ILogger = logger.get_logger("ui")
        self.clients = clients

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal(id="buttons"):
            self._structlog.info("current_tab", current_tab=self.current_tab)
            yield Button(
                decorated_tab("Dashboard", "dashboard", self.current_tab),
                id="dashboard",
            )
            yield Button(
                decorated_tab("Job Visualizer", "jobviz", self.current_tab), id="jobviz"
            )
            yield Button(
                decorated_tab("Contest", "contest", self.current_tab), id="contest"
            )
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
        btn_id = event.button.id
        if btn_id in ["dashboard", "jobviz", "contest"]:
            self._structlog.info("button", btn=btn_id)
            self.current_tab = btn_id
            self.query_one(ContentSwitcher).current = btn_id

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

    def action_next_tab(self) -> None:
        """Switch ContentSwitcher to the next view."""
        switcher = self.query_one(ContentSwitcher)
        views = [child.id for child in switcher.children if isinstance(child.id, str)]
        if not views:
            return
        try:
            current = (
                switcher.current if isinstance(switcher.current, str) else views[0]
            )
            current_index = views.index(current)
        except ValueError:
            current_index = 0
        next_index = (current_index + 1) % len(views)
        self.current_tab = views[next_index]
        switcher.current = views[next_index]
