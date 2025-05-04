from typing import List, Callable, Awaitable

from agentarena.models.arena import Arena
from agentarena.models.arena import ArenaDTO
from agentarena.models.arenaagent import ArenaAgent
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.feature import Feature
from agentarena.models.feature import FeatureDTO
from agentarena.services.model_service import ModelService
import structlog

log = structlog.get_logger(module="container.arena")


async def make_arena(
    arena_config: ArenaDTO,
    arenaagent_service: ModelService[ArenaAgentDTO] = None,
    feature_service: ModelService[FeatureDTO] = None,
    make_arenaagent: Callable[[ArenaAgentDTO], Awaitable[ArenaAgent]] = None,
) -> Arena:
    """
    Create an arena object from the arena configuration.

    Args:
        arena_config: The arena configuration
        agentarena_service: The agentarena service

    Returns:
        The arena object
    """
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
        await make_arenaagent(arena_agent) for arena_agent in arenaagents
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
