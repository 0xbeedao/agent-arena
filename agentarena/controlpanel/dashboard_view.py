"""Dashboard View for Control Panel UI using Textual."""

from textual.reactive import reactive
from textual.widgets import Collapsible
from textual.widgets import DataTable
from textual.widgets import Label
from textual.widgets import Static

from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.factories.logger_factory import LoggingService


class DashboardView(Static):
    """Main content panel."""

    arenas = reactive([], recompose=True)
    contests = reactive([], recompose=True)
    participants = reactive([], recompose=True)
    strategies = reactive([], recompose=True)
    arenas_expanded = reactive(False)
    contests_expanded = reactive(True)
    participants_expanded = reactive(False)
    strategies_expanded = reactive(False)

    def __init__(self, clients: dict, logger: LoggingService):
        super().__init__()
        self._structlog: ILogger = logger.get_logger("dashboard")
        self.clients = clients

    def compose(self):
        """Compose dashboard view."""
        with Collapsible(
            collapsed=not self.contests_expanded,
            title="Contests",
            id="load-contests",
        ):
            yield DataTable(id="contest-table", classes="contest-table")

        with Collapsible(
            collapsed=not self.arenas_expanded,
            title="Arenas",
            id="load-arenas",
        ):
            yield DataTable(id="arena-table", classes="arena-table")

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

    async def load_arenas(self, log: ILogger) -> None:
        client = self.clients["arena"]
        assert client, "Missing Arena client"
        log = log.bind(action="loading arenas")
        log.info("starting")
        try:
            arenas = await client.get("/api/arena/")
            self.arenas = arenas  # Assign new list to trigger reactive update
            log.info(f"Loaded {len(arenas)}")
            log.info(arenas=arenas)
            rows = [
                [
                    a["name"],
                    a["id"],
                    a["description"],
                    a["height"],
                    a["width"],
                    a["max_random_features"],
                ]
                for a in self.arenas
            ]
            table = self.query_one("#arena-table", DataTable)
            table.clear()
            table.add_column("Name", width=20)
            table.add_column("ID", width=30)
            table.add_column("Description", width=40)
            table.add_column("Height", width=6)
            table.add_column("Width", width=6)
            table.add_column("Feats", width=6)
            table.add_rows(rows)
            table.refresh()
        except Exception as e:
            log.error(f"Error loading arenas: {str(e)}")
            self.notify(f"Error loading arenas: {str(e)}", severity="error")

    async def load_contests(self, log: ILogger) -> None:
        client = self.clients["arena"]
        assert client, "Missing Arena client"
        log = log.bind(action="loading contests")
        log.info("starting")
        try:
            contests = await client.get("/api/contest")
            self.contests = contests  # Assign new list to trigger reactive update
            log.info(f"Loaded {len(contests)}")
            log.info(contests=contests)
            rows = [
                [c["id"], c["round"]["round_no"] if c["round"] else "-1", c["state"]]
                for c in self.contests
            ]
            table = self.query_one("#contest-table", DataTable)
            table.clear()
            table.add_column("ID", width=30)
            table.add_column("Round", width=5)
            table.add_column("State", width=10)
            table.add_rows(rows)
            table.refresh()
        except Exception as e:
            log.error(f"Error loading contests: {str(e)}")
            self.notify(f"Error loading contests: {str(e)}", severity="error")

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

        # Update expanded state
        if event_id == "load-arenas":
            self.arenas_expanded = True
        elif event_id == "load-contests":
            self.contests_expanded = True
        elif event_id == "load-participants":
            self.participants_expanded = True
        elif event_id == "load-strategies":
            self.strategies_expanded = True
        if event_id == "load-arenas":
            await self.load_arenas(log)
        elif event_id == "load-participants":
            await self.load_participants(log)
        elif event_id == "load-contests":
            log.info("loading contests")
            await self.load_contests(log)
        elif event_id == "load-strategies":
            log.info("loading strategies")
            await self.load_strategies(log)
        else:
            log.info("not handled")

    async def on_data_table_cell_selected(self, event: DataTable.CellSelected) -> None:
        # Only handle clicks in the contest-table
        if event.data_table.id != "contest-table":
            return
        row, col = event.coordinate
        # Only handle clicks in the ID column
        if col != 0:
            return
        contest_id = event.value
        # Find the contest object
        contest = next((c for c in self.contests if c["id"] == contest_id), None)
        if contest:
            # Notify the app to show this contest
            await self.app.show_contest(contest)
