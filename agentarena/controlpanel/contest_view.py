"""Dashboard View for Control Panel UI using Textual."""

import asyncio
from datetime import datetime

from nats.aio.msg import Msg
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable
from textual.widgets import Label
from textual.widgets import Static

from agentarena.controlpanel.components import StatusLabel
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
        self.subscriptions = {}

    async def _subscribe(self, contest_id: str):
        self.subscriptions[contest_id] = await self.clients["arena"].subscribe(
            f"arena.contest.{contest_id}.contestflow.*", self.handle_flow
        )

    async def _unsubscribe(self, contest_id: str):
        if contest_id in self.subscriptions:
            await self.subscriptions[contest_id].unsubscribe()
            del self.subscriptions[contest_id]

    async def handle_flow(self, msg: Msg):
        self._structlog.info("flow", msg=msg)
        title = ".".join(msg.subject.split(".")[3:])
        self.notify(
            msg.subject,
            title=title,
            timeout=5,
            severity="information",
        )
        if self.contest:
            self.contest = await self.clients["arena"].get(
                f"/api/contest/{self.contest['id']}"
            )

    def watch_contest(self, contest):
        # When contest changes, unsubscribe from all and subscribe to new contest

        async def update_subscriptions():
            # Unsubscribe from all current subscriptions
            for contest_id in list(self.subscriptions.keys()):
                await self._unsubscribe(contest_id)
            # Subscribe to new contest if it exists
            if contest and "id" in contest:
                await self._subscribe(contest["id"])
            self.refresh()

        asyncio.create_task(update_subscriptions())

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
                yield StatusLabel(self.contest["state"])

                if "rounds" in self.contest and self.contest["rounds"]:
                    round = self.contest["rounds"][0]
                    with Vertical(id=f"round-{round['round_no']}"):
                        yield Label(f"Round Number: {round['round_no']}")
                        yield StatusLabel(round["state"])
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
