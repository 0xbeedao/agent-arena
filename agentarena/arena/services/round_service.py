from agentarena.arena.models import ContestRound, ContestRoundCreate
from agentarena.core.services.model_service import ModelService


class RoundService(ModelService[ContestRound, ContestRoundCreate]):
    """
    Service for managing contest rounds.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
