from typing import List
from dependency_injector.wiring import Provide, inject
from fastapi import Depends

from agentarena.config.containers import Container
from agentarena.models.agent import AgentDTO
from agentarena.models.arena import Arena, ArenaDTO
from agentarena.models.arenaagent import ArenaAgent, ArenaAgentDTO
from agentarena.models.contest import Contest, ContestDTO, ContestStatus
from agentarena.models.feature import Feature, FeatureDTO
from agentarena.models.strategy import Strategy, StrategyDTO
from agentarena.services.model_service import ModelService
import structlog

log = structlog.getLogger("builder_service")

@inject
async def make_arena(
    arena_config: ArenaDTO,
    arenaagent_service: ModelService[ArenaAgentDTO] = Depends(Provide[Container.arenaagent_service]),
    feature_service: ModelService[FeatureDTO] = Depends(Provide[Container.feature_service]),
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
    featureDTOs: List[FeatureDTO] = await feature_service.get_where("arena_config_id = :id", {"id": arena_config.id})
    features = [Feature.from_dto(feature) for feature in featureDTOs]

    # Get the Agents
    arenaagents: List[ArenaAgentDTO] = await arenaagent_service.get_where("arena_config_id = :id", {"id": arena_config.id})

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
        agents=agentResponses
    )

@inject
async def make_arenaagent(
    arena_agent: ArenaAgentDTO,
    logger=log,
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
    strategy_service: ModelService[StrategyDTO] = Depends(Provide[Container.strategy_service]),
) -> ArenaAgent:
    """
    Create an arena agent object from the arena agent configuration.

    Args:
        arenaagent_config: The arena agent configuration
        agent_service: The agent service
        strategy_service: The strategy service

    Returns:
        The arena agent object
    """
    boundlog = logger.bind(arenaagent=arena_agent.id)
    boundlog.info("Making arenaagent")

    # Get the Agent
    [agentDTO, _] = await agent_service.get(arena_agent.agent_id)

    # Get the Strategy
    [strategyDTO, _] = await strategy_service.get(agentDTO.strategy_id)

    strategy: Strategy = Strategy.from_dto(strategyDTO)
    boundlog.debug(f"Got strategy #{agentDTO.strategy_id}")

    return ArenaAgent(
        id=arena_agent.id,
        role=arena_agent.role,
        agent_id=agentDTO.id,
        name=agentDTO.name,
        description=agentDTO.description,
        strategy=strategy
    )

@inject
async def make_contest(
    contestDTO: ContestDTO,
    arena_service: ModelService[ArenaDTO] = Depends(Provide[Container.arena_service]),
    arenaagent_service: ModelService[ArenaAgentDTO] = Depends(Provide[Container.arenaagent_service]),
) -> Contest:
    """
    Create a contest object from the contest configuration.

    Args:
        contest_id: The contest ID
        contest_service: The contest service

    Returns:
        The contest object
    """
    boundlog = log.bind(contest=contestDTO.arena_config_id)
    boundlog.info("making contest")
    [arenaDTO, response] = await arena_service.get(contestDTO.arena_config_id)
    if not response.success:
        raise ValueError(f"Arena with ID {contestDTO.arena_config_id} not found")
    
    boundlog.info(f"got arenaDTO: {arenaDTO}")
    arena = await make_arena(arenaDTO)
    boundlog.info(f"got arena: {arena.id}")
    
    winner = None
    if contestDTO.winner is not None:
        boundlog.info("Found a winner, loading it: {}", contestDTO.winnner)
        aa, _ = await arenaagent_service.get(contestDTO.winner)
        winner, _ = await make_arenaagent(aa, logger=boundlog)

    positions: List[str] = contestDTO.player_positions.split(';')
    boundlog.info(f"positions: {positions}")

    return Contest(
        id=contestDTO.id,
        arena=arena,
        current_round=contestDTO.current_round,
        player_positions=positions,
        status=ContestStatus(contestDTO.status),
        start_time=contestDTO.start_time,
        end_time=contestDTO.end_time,
        winner=winner,
    )
    