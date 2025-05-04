from agentarena.models.agent import AgentDTO
from agentarena.models.arenaagent import ArenaAgent
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.strategy import Strategy
from agentarena.models.strategy import StrategyDTO
from agentarena.services.model_service import ModelService


async def arenaagent_factory(
    arena_agent: ArenaAgentDTO,
    agent_service: ModelService[AgentDTO] = None,
    strategy_service: ModelService[StrategyDTO] = None,
    make_logger=None,
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
    log = make_logger.bind(arenaagent=arena_agent.id)
    log.info("Making arenaagent")

    # Get the Agent
    [agentDTO, _] = await agent_service.get(arena_agent.agent_id)

    # Get the Strategy
    [strategyDTO, _] = await strategy_service.get(agentDTO.strategy_id)

    strategy: Strategy = Strategy.from_dto(strategyDTO)
    log.debug(f"Got strategy #{agentDTO.strategy_id}")

    return ArenaAgent(
        id=arena_agent.id,
        role=arena_agent.role,
        agent_id=agentDTO.id,
        name=agentDTO.name,
        description=agentDTO.description,
        strategy=strategy,
    )
