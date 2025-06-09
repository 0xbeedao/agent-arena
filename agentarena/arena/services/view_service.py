from agentarena.arena.models import Contest
from agentarena.arena.models import Participant
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.public import ContestPublic


class ViewService:
    """Service for managing views of Contests - allowing different players to have a different view."""

    def __init__(self, logging: LoggingService):
        self.log = logging.get_logger("service")

    def get_contest_view(self, contest: Contest, player: Participant) -> ContestPublic:
        """Get a view of the contest tailored to the player."""
        view = contest.get_public()
        log = self.log.bind(contest_id=contest.id, player_id=player.id)
        for participant in view.participants:
            if participant.id != player.id:
                participant.endpoint = ""

        if view.rounds:
            for round in view.rounds:
                for other in round.players:
                    if other.id != player.id:
                        other.inventory = []
                        other.score = 0

        log.debug("returning view", view=view)
        return view
