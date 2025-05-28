"""Control Panel UI using Textual."""

from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Collapsible
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Label
from textual.widgets import Static
from textual.widgets import ContentSwitcher

from agentarena.core.factories.logger_factory import ILogger, LoggingService


class DashboardView(Static):
    """Main content panel."""

    current_view = reactive("dashboard")
    participants = reactive([], recompose=True)
    strategies = reactive([], recompose=True)

    def __init__(self, clients: dict, logger: LoggingService):
        super().__init__()
        self._structlog: ILogger = logger.get_logger("ui")
        self.clients = clients

    def compose(self):
        """Compose dashboard view."""
        self._structlog.info("participants", p=self.participants)
        with Collapsible(
            collapsed=len(self.participants) == 0,
            title="Participants",
            id="load-participants",
        ):
            if not self.participants:
                yield Label("Loading ...")
            else:
                for participant in self.participants:
                    yield Label(participant["name"])
        with Collapsible(collapsed=True, title="Strategies", id="load-strategies"):
            if not self.strategies:
                yield Label("Loading ...")
            else:
                for strategy in self.strategies:
                    yield Label(strategy["name"])

    async def load_participants(self, log: ILogger) -> None:
        client = self.clients["arena"]
        assert client, "Missing Arena client"
        log = log.bind(action="loading participants")
        log.info("starting")
        try:
            participants = await client.get_participants()
            self.participants = (
                participants  # Assign new list to trigger reactive update
            )
            log.info(f"Loaded {len(participants)}")
            self.refresh()
        except Exception as e:
            log.error(f"Error loading participants: {str(e)}")
            self.notify(f"Error loading participants: {str(e)}", severity="error")

    async def load_strategies(self, log: ILogger) -> None:
        client = self.clients["actor"]
        assert client, "Missing Actor client"
        log = log.bind(action="loading strategies")
        log.info("starting")
        try:
            strats = await client.get("/api/strategy")
            self.strategies = strats  # Assign new list to trigger reactive update
            log.info(f"Loaded {len(strats)}")
            self.refresh()
        except Exception as e:
            log.error(f"Error loading strategies: {str(e)}")
            self.notify(f"Error loading strategies: {str(e)}", severity="error")

    async def on_collapsible_expanded(self, event: Collapsible.Expanded) -> None:
        """Handle button presses in main panel."""
        event_id = event.collapsible.id
        log = self._structlog.bind(trigger=event_id)
        if event_id == "load-participants":
            await self.load_participants(log)
        elif event_id == "load-strategies":
            log.info("loading strategies")
            await self.load_strategies(log)
        else:
            log.info("not handled")


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
            yield Button("Contests", id="contests")
        with ContentSwitcher(initial="dashboard"):
            with Vertical(id="dashboard"):
                yield DashboardView(self.clients, self.loggingservice)
            with Vertical(id="jobviz"):
                yield Label("Job Visualizer Content")
            with Vertical(id="contests"):
                Label("Contests Content")
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
