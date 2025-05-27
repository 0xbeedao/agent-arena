"""Control Panel UI using Textual."""

from textual.app import App
from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import Button
from textual.widgets import Footer
from textual.widgets import Header
from textual.widgets import Label
from textual.widgets import Static


class Sidebar(Static):
    """Sidebar navigation panel."""

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Button("Dashboard", id="dashboard-btn")
            yield Button("Job Visualizer", id="jobviz-btn")
            yield Button("Contests", id="contests-btn")


class MainPanel(Static):
    """Main content panel."""

    current_view = reactive("dashboard")
    participants = reactive([])

    def __init__(self, clients={}):
        super().__init__()
        self.clients = clients

    def compose_dashboard(self) -> Vertical:
        """Compose dashboard view."""
        container = Vertical()
        container.compose_add_child(
            Button("Load Participants", id="load-participants-btn")
        )
        if self.participants:
            container.compose_add_child(Label("Participants:"))
            for participant in self.participants:
                container.compose_add_child(Label(participant["name"]))
        return container

    def watch_current_view(self, view_name: str) -> None:
        """Update view when current_view changes."""
        self.remove_children()
        if view_name == "dashboard":
            self.mount(self.compose_dashboard())
        elif view_name == "jobviz":
            self.mount(Label("Job Visualizer Content"))
        elif view_name == "contests":
            self.mount(Label("Contests Content"))

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses in main panel."""
        if event.button.id == "load-participants-btn":
            client = self.clients["arena"]
            assert client, "Missing Arena client"
            try:
                self.participants = await client.get_participants()
                self.current_view = "dashboard"  # Refresh the view
            except Exception as e:
                self.notify(f"Error loading participants: {str(e)}", severity="error")


class StatusBar(Static):
    """Status bar at bottom of screen."""

    def compose(self) -> ComposeResult:
        yield Label("Ready", id="status-message")
        yield Label("", id="status-controls")


class ControlPanelUI(App):
    """Main UI application."""

    CSS_PATH = "controlpanel.css"

    def __init__(self, clients={}):
        super().__init__()
        self.clients = clients

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield MainPanel(self.clients)
        yield StatusBar()
        yield Footer()

    def setup(self) -> None:
        """Setup the UI components."""

    def main_loop(self) -> None:
        """Run the main UI loop."""
        self.run()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        if button_id == "dashboard-btn":
            self.query_one(MainPanel).current_view = "dashboard"
        elif button_id == "jobviz-btn":
            self.query_one(MainPanel).current_view = "jobviz"
        elif button_id == "contests-btn":
            self.query_one(MainPanel).current_view = "contests"
        elif button_id == "load-participants-btn":
            await self.query_one(MainPanel).on_button_pressed(event)
