from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.agent import AgentDTO
from agentarena.models.participant import Participant
from agentarena.models.participant import ParticipantDTO
from agentarena.services.model_service import ModelService


class ParticipantFactory:

    def __init__(
        self,
        agent_service: ModelService[AgentDTO] = None,
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.agent_service = agent_service
        self.log = logging.get_logger("participant_factory")

    async def build(self, participant: ParticipantDTO) -> Participant:
        """
        Create a participant object from the participant configuration.

        Args:
            participant_config: The participant configuration
            agent_service: The agent service
            strategy_service: The strategy service

        Returns:
            The participant object
        """
        log = self.log.bind(
            module="participant_factory",
            participant="none" if participant is None else participant.id,
        )
        if participant is None:
            log.warn("Null agent")
            return None
        log.info("Making participant")

        # Get the Agent
        [agentDTO, _] = await self.agent_service.get(participant.agent_id)

        return Participant(
            id=participant.id,
            role=participant.role,
            agent_id=agentDTO.id,
            name=agentDTO.name,
            description=agentDTO.description,
        )
