"""Control Panel Main Application."""

import os

import typer
import yaml

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.util.files import find_file_upwards

from .clients import ActorClient
from .clients import ArenaClient
from .clients import MessageBrokerClient
from .clients import SchedulerClient
from .ui import ControlPanelUI

prod = getattr(os.environ, "ARENA_ENV", "dev") == "prod"


def read_config():
    yamlfile = find_file_upwards("agent-arena-config.yaml")
    assert yamlfile, "Where is my config file?"
    with open(yamlfile, "r") as f:
        yaml_data = yaml.safe_load(f)
    return yaml_data


class ControlPanelApp:
    """Main control panel application class."""

    def __init__(self):
        config = read_config()
        logger = LoggingService(
            capture=False,
            prod=prod,
            level="DEBUG",
            name="control",
        )
        self._structlog = logger.get_logger("control")
        clients = {
            "arena": ArenaClient(config["arena"]),
            "scheduler": SchedulerClient(config["scheduler"]),
            "actor": ActorClient(config["actor"]),
            "broker": MessageBrokerClient(config["messagebroker"]),
        }
        self.config = config
        self.ui = ControlPanelUI(clients, logger)
        self.clients = clients
        self._structlog.info("setup complete")

    def run(self):
        """Run the control panel application."""
        self.ui.setup()
        self._structlog.info("starting main loop")
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
