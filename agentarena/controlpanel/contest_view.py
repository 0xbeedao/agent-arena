"""Dashboard View for Control Panel UI using Textual."""

import asyncio
from datetime import datetime

from nats.aio.msg import Msg
from textual.containers import Horizontal
from textual.containers import Vertical
from textual.reactive import reactive
from textual.widgets import DataTable
from textual.widgets import Collapsible
from textual.widgets import Label
from textual.widgets import Markdown
from textual.widgets import Button
from textual.widgets import Static
from textual.widgets import Rule

from agentarena.models.constants import ContestState
from agentarena.controlpanel.components import StatusLabel
from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.factories.logger_factory import LoggingService


def safe_format_time(contest, key: str):
    if contest and key in contest and contest[key] is not None and contest[key] > 0:
        return format_time(contest[key])
    return "N/A"


def format_time(timestamp):
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


class ContestButtons(Static):
    def __init__(self, contest: dict | None):
        super().__init__()
        self.contest = contest

    def compose(self):
        starting = False
        if self.contest and self.contest["state"] == ContestState.CREATED:
            starting = True
        yield Button("Start Round", id="start-round", disabled=(not starting))
        yield Button("Advance Round", id="advance-round", disabled=starting)


class FeaturesTable(Static):
    def __init__(self, features: list):
        super().__init__()
        self.features = features

    def compose(self):
        with Collapsible(
            collapsed=True,
            title="Features",
            id="round-features",
        ):
            # Features table
            features_table = DataTable(id="features-table")
            features_table.add_column("Name", width=20)
            features_table.add_column("Position", width=10)
            features_table.add_column("Description", width=None)
            features_rows = [
                [f["name"], f["position"], f["description"]] for f in self.features
            ]
            features_table.add_rows(features_rows)
            yield features_table


class PlayersTable(Static):
    def __init__(self, players: list):
        super().__init__()
        self.players = players

    def compose(self):
        with Collapsible(
            collapsed=True,
            title="Players",
            id="round-players",
        ):
            # Players table
            players_table = DataTable(id="players-table")
            players_table.add_column("Name", width=20)
            players_table.add_column("Position", width=10)
            players_table.add_column("Inventory", width=20)
            players_table.add_column("Health", width=10)
            player_rows = [
                [p["name"], p["position"], p["inventory"], p["health"]]
                for p in self.players
            ]
            players_table.add_rows(player_rows)
            yield players_table


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
        self._structlog.info("subscribing to contest", contest_id=contest_id)
        self.subscriptions[contest_id] = await self.clients["broker"].subscribe(
            f"arena.contest.{contest_id}.contestflow.>", self.handle_flow
        )

    async def _unsubscribe(self, contest_id: str):
        self._structlog.info("unsubscribing from contest", contest_id=contest_id)
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
        self._structlog = self._structlog.bind(contest=contest)
        self._structlog.info("watch_contest")

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
        with Horizontal(id="contest-page"):
            with Vertical(id="contest-primary"):
                with Horizontal(id="contest-header"):
                    if self.contest:
                        yield Label(
                            f"[bold][yellow]{self.contest['arena']['name']}[/yellow][/bold]  "
                        )
                        yield Label(
                            f"Start Time: {safe_format_time(self.contest, 'start_time')}  "
                        )
                        yield Label(
                            f"End Time: {safe_format_time(self.contest, 'end_time')}  "
                        )
                        yield StatusLabel(self.contest["state"])
                        yield Label(f'  {self.contest["id"]}')
                    else:
                        yield Label("Contest: None")
                if self.contest:
                    yield Label(self.contest["arena"]["description"])
                yield Rule()
                if self.contest and "rounds" in self.contest:
                    for round in self.contest["rounds"]:
                        yield Label(f"Round Number: {round['round_no']}")
                        yield StatusLabel(round["state"])
                        yield Label("Narrative:")
                        yield Markdown(round["narrative"])
                        yield FeaturesTable(round["features"])
                        yield PlayersTable(round["players"])
                        yield Rule()
            with Vertical(id="contest-actions"):
                yield ContestButtons(self.contest)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        cmd = event.button.id
        self._structlog.info("button", btn=cmd)
        if self.contest:
            if cmd == "start-round":
                await self.clients["arena"].post(
                    f"/api/contest/{self.contest['id']}/start", None
                )
            elif cmd == "advance-round":
                await self.clients["arena"].post(
                    f"/api/contest/{self.contest['id']}/advance", None
                )
        else:
            self._structlog.error("no contest for command", cmd=cmd)
