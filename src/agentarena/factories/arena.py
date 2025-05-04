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

log = structlog.get_logger(module="container.arena")


async def arena_factory(
    arena_config: ArenaDTO,
    arenaagent_service: ModelService[ArenaAgentDTO] = None,
    feature_service: ModelService[FeatureDTO] = None,
    arenaagent_factory: Callable[[ArenaAgentDTO], Awaitable[ArenaAgent]] = None,
    make_logger=None,
) -> Arena:
    """
    Create an arena object from the arena configuration.

    Args:
        arena_config: The arena configuration
        agentarena_service: The agentarena service

    Returns:
        The arena object
    """
    log = make_logger(module="arena_factory", arena_id=arena_config.id)
    log.info(f"Making arena: #{arena_config.id}")
    # Get the features
    featureDTOs: List[FeatureDTO] = await feature_service.get_where(
        "arena_config_id = :id", {"id": arena_config.id}
    )
    features = [Feature.from_dto(feature) for feature in featureDTOs]

    # Get the Agents
    arenaagents: List[ArenaAgentDTO] = await arenaagent_service.get_where(
        "arena_config_id = :id", {"id": arena_config.id}
    )

    agentResponses: List[ArenaAgent] = [
        await arenaagent_factory(arena_agent) for arena_agent in arenaagents
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
