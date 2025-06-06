"""Dashboard View for Control Panel UI using Textual."""

from datetime import datetime
from typing import Dict, List

from textual.reactive import reactive
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.widgets import Collapsible
from textual.widgets import DataTable
from textual.widgets import Label
from textual.widgets import Static

from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.factories.logger_factory import LoggingService


def safe_format_time(contest, key: str):
    if contest and key in contest and contest[key] is not None and contest[key] > 0:
        return format_time(contest[key])
    return "N/A"


def format_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


class ContestView(Static):
    """Contest Control Panel View"""

    current_view = reactive("dashboard")
    contest = reactive(None, recompose=True)

    def __init__(self, clients: dict, logger: LoggingService):
        super().__init__()
        self._structlog: ILogger = logger.get_logger("contest")
        self.clients = clients

    def watch_contest(self, contest):
        # Update the label when contest changes
        self.refresh()

    def compose(self):
        """Compose dashboard view."""
        with Horizontal(id="contest-header"):
            yield Label("Contest:")
            if self.contest:
                yield Label(self.contest["id"])
                yield Label(f"Name {self.contest['arena']['name']}")
            else:
                yield Label("Contest: None")
        if self.contest:
            with Vertical(id="contest-details"):
                yield Label(f"Name: {self.contest['arena']['name']}")
                yield Label(f"Description: {self.contest['arena']['description']}")
                yield Label(
                    f"Start Time: {safe_format_time(self.contest, 'start_time')}"
                )
                yield Label(f"End Time: {safe_format_time(self.contest, 'end_time')}")
                yield Label(f"State: {self.contest['state']}")

                if self.contest["round"]:
                    round = self.contest["round"]
                    with Vertical(id=f"round-{round['round_no']}"):
                        yield Label(f"Round Number: {round['round_no']}")
                        yield Label(f"State: {round['state']}")
                        yield Label(
                            f"Start Time: {safe_format_time(round, 'start_time')}"
                        )
                        yield Label(f"End Time: {safe_format_time(round, 'end_time')}")
                        yield Label(f"Narrative: {round['narrative']}")
                        yield Label("Features:")
                        # Features table
                        features_table = DataTable(id="features-table")
                        features_table.add_column("Name", width=20)
                        features_table.add_column("Description", width=40)
                        features_table.add_column("Position", width=10)
                        features_rows = [
                            [f["name"], f["description"], f["position"]]
                            for f in round["features"]
                        ]
                        features_table.add_rows(features_rows)
                        yield features_table

                        # Players table
                        players_table = DataTable(id="players-table")
                        players_table.add_column("Name", width=20)
                        players_table.add_column("Position", width=10)
                        players_table.add_column("Inventory", width=20)
                        players_table.add_column("Health", width=10)
                        player_rows = [
                            [p["name"], p["position"], p["inventory"], p["health"]]
                            for p in round["players"]
                        ]
                        players_table.add_rows(player_rows)
                        yield players_table
