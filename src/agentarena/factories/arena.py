from typing import Awaitable
from typing import Callable
from typing import List

from agentarena.models.arena import Arena
from agentarena.models.arena import ArenaDTO
from agentarena.models.arenaagent import ArenaAgent
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.feature import Feature
from agentarena.models.feature import FeatureDTO
from agentarena.services.model_service import ModelService


class ArenaFactory:

    def __init__(
        self,
        arenaagent_service: ModelService[ArenaAgentDTO] = None,
        feature_service: ModelService[FeatureDTO] = None,
        arenaagent_factory: Callable[[ArenaAgentDTO], Awaitable[ArenaAgent]] = None,
        logging=None,
    ):
        self.arenaagent_service = arenaagent_service
        self.feature_service = feature_service
        self.arenaagent_factory = arenaagent_factory
        self.log = logging.get_logger(module="arena_factory")

    async def build(
        self,
        arena_config: ArenaDTO,
    ) -> Arena:
        """
        Create an arena object from the arena configuration.

        Args:
            arena_config: The arena configuration
            agentarena_service: The agentarena service

        Returns:
            The arena object
        """
        log = self.log.bind(
            arena_id="none" if arena_config is None else arena_config.id,
        )
        log.info(f"Making arena")
        if arena_config is None:
            return None
        # Get the features
        featureDTOs: List[FeatureDTO] = await self.feature_service.get_where(
            "arena_config_id = :id", {"id": arena_config.id}
        )
        features = [Feature.from_dto(feature) for feature in featureDTOs]

        # Get the Agents
        arenaagents: List[ArenaAgentDTO] = await self.arenaagent_service.get_where(
            "arena_config_id = :id", {"id": arena_config.id}
        )

        builder = self.arenaagent_factory.build
        agentResponses: List[ArenaAgent] = [
            await builder(arena_agent) for arena_agent in arenaagents
        ]

        return Arena(
            id=arena_config.id,
            name=arena_config.name,
            description=arena_config.description,
            height=arena_config.height,
            width=arena_config.width,
            rules=arena_config.rules,
            max_random_features=arena_config.max_random_features,
            features=features,
            agents=agentResponses,
        )
