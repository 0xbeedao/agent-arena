"""Control Panel UI using Textual."""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Header, Footer, Static, Button, Tree, Label
from textual.reactive import reactive
from typing import Dict, Any


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

    def watch_current_view(self, view_name: str) -> None:
        """Update view when current_view changes."""
        self.remove_children()
        if view_name == "dashboard":
            self.mount(Label("Dashboard Content"))
        elif view_name == "jobviz":
            self.mount(Label("Job Visualizer Content"))
        elif view_name == "contests":
            self.mount(Label("Contests Content"))


class StatusBar(Static):
    """Status bar at bottom of screen."""

    def compose(self) -> ComposeResult:
        yield Label("Ready", id="status-message")
        yield Label("", id="status-controls")


class ControlPanelUI(App):
    """Main UI application."""

    CSS_PATH = "controlpanel.css"

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        with Horizontal():
            yield Sidebar()
            yield MainPanel()
        yield StatusBar()
        yield Footer()

    def setup(self) -> None:
        """Setup the UI components."""
        pass

    def main_loop(self) -> None:
        """Run the main UI loop."""
        self.run()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle sidebar button presses."""
        button_id = event.button.id
        if button_id == "dashboard-btn":
            self.query_one(MainPanel).current_view = "dashboard"
        elif button_id == "jobviz-btn":
            self.query_one(MainPanel).current_view = "jobviz"
        elif button_id == "contests-btn":
            self.query_one(MainPanel).current_view = "contests"
