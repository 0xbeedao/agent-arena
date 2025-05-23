"""Control Panel Main Application."""

import typer

from .clients import ActorClient
from .clients import ArenaClient
from .clients import SchedulerClient
from .ui import ControlPanelUI


class ControlPanelApp:
    """Main control panel application class."""

    def __init__(self):
        self.ui = ControlPanelUI()
        self.clients = {
            "arena": ArenaClient(),
            "scheduler": SchedulerClient(),
            "actor": ActorClient(),
        }

    def run(self):
        """Run the control panel application."""
        self.ui.setup()
        self.ui.main_loop()


app = typer.Typer()


@app.command()
def start(
    host: str = typer.Option("localhost", help="API server host"),
    port: int = typer.Option(8000, help="API server port"),
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """Start the control panel application."""
    control_panel = ControlPanelApp()
    control_panel.run()


if __name__ == "__main__":
    app()
