"""Dashboard View for Control Panel UI using Textual."""

from textual.reactive import reactive
from textual.widgets import Collapsible
from textual.widgets import DataTable
from textual.widgets import Label
from textual.widgets import Static

from agentarena.core.factories.logger_factory import ILogger
from agentarena.core.factories.logger_factory import LoggingService


class ConteestView(Static):
    """Contest Control Panel View"""

    current_view = reactive("dashboard")
    arenas = reactive([], recompose=True)
    contests = reactive([], recompose=True)
    participants = reactive([], recompose=True)
    strategies = reactive([], recompose=True)
    arenas_expanded = reactive(False)
    contests_expanded = reactive(False)
    participants_expanded = reactive(False)
    strategies_expanded = reactive(False)

    def __init__(self, clients: dict, logger: LoggingService):
        super().__init__()
        self._structlog: ILogger = logger.get_logger("dashboard")
        self.clients = clients

    def compose(self):
        """Compose dashboard view."""
        with Collapsible(
            collapsed=not self.arenas_expanded,
            title="Arenas",
            id="load-arenas",
        ):
            yield DataTable(id="arena-table", classes="arena-table")

        with Collapsible(
            collapsed=not self.contests_expanded,
            title="Contests",
            id="load-contests",
        ):
            yield DataTable(id="contest-table", classes="contest-table")

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
