from agentarena.models.agent import AgentDTO
from agentarena.models.arenaagent import ArenaAgent
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.strategy import Strategy
from agentarena.models.strategy import StrategyDTO
from agentarena.services.model_service import ModelService


class ArenaAgentFactory:

    def __init__(
        self,
        agent_service: ModelService[AgentDTO] = None,
        strategy_service: ModelService[StrategyDTO] = None,
        logging=None,
    ):
        self.agent_service = agent_service
        self.strategy_service = strategy_service
        self.log = logging.get_logger(module="ArenaAgentFactory")

    async def build(self, arena_agent: ArenaAgentDTO) -> ArenaAgent:
        """
        Create an arena agent object from the arena agent configuration.

        Args:
            arenaagent_config: The arena agent configuration
            agent_service: The agent service
            strategy_service: The strategy service

        Returns:
            The arena agent object
        """
        log = self.log.bind(
            module="arenaagent_factory",
            arenaagent="none" if arena_agent is None else arena_agent.id,
        )
        if arena_agent is None:
            log.warn("Null agent")
            return None
        log.info("Making arenaagent")

        # Get the Agent
        [agentDTO, _] = await self.agent_service.get(arena_agent.agent_id)

        # Get the Strategy
        [strategyDTO, _] = await self.strategy_service.get(agentDTO.strategy_id)

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
