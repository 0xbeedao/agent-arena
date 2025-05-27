"""Control Panel Main Application."""

import typer
import yaml

from agentarena.util.files import find_file_upwards

from .clients import ActorClient
from .clients import ArenaClient
from .clients import MessageBrokerClient
from .clients import SchedulerClient
from .ui import ControlPanelUI


def read_config():
    yamlfile = find_file_upwards("agent-arena-config.yaml")
    assert yamlfile, "Where is my config file?"
    with open(yamlfile, "r") as f:
        yaml_data = yaml.safe_load(yamlfile)
    return yaml_data


class ControlPanelApp:
    """Main control panel application class."""

    def __init__(self):
        self.ui = ControlPanelUI()
        self.config = read_config()
        self.clients = {
            "arena": ArenaClient(self.config.arena),
            "scheduler": SchedulerClient(self.config.scheduler),
            "actor": ActorClient(self.config.actor),
            "broker": MessageBrokerClient(self.config.messagebroker),
        }

    def run(self):
        """Run the control panel application."""
        self.ui.setup()
        self.ui.main_loop()


app = typer.Typer()


@app.command()
def start(
    debug: bool = typer.Option(False, help="Enable debug mode"),
):
    """Start the control panel application."""
    control_panel = ControlPanelApp()
    control_panel.run()


if __name__ == "__main__":
    app()
