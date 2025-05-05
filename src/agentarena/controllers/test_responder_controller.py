from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from agentarena.controllers import responder_controller
from agentarena.models.participant import ParticipantDTO
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus


@pytest.fixture
def mock_participant_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_logging():
    logger = Mock()
    logger.get_logger.return_value = logger
    logger.info = Mock()
    return logger


@pytest.fixture
def mock_participant_factory():
    factory = AsyncMock()
    return factory


@pytest.mark.asyncio
async def test_healthcheck_success(
    mock_participant_service, mock_logging, mock_participant_factory
):
    # Arrange
    participant_id = "aa1"
    job_id = "job42"
    agent_dto = ParticipantDTO(
        arena_config_id="arena1", agent_id="agent1", role="player"
    )
    mock_participant_service.get.return_value = (agent_dto, Mock(success=True))
    agent = Mock()
    agent.name = "AgentName"
    mock_participant_factory.build.return_value = agent

    # Act
    result = await responder_controller.healthcheck(
        participant_id=participant_id,
        job_id=job_id,
        participant_service=mock_participant_service,
        logging=mock_logging,
        participant_factory=mock_participant_factory,
    )

    # Assert
    assert isinstance(result, HealthResponse)
    assert result.status == "completed"
    assert result.job_id == job_id
    assert isinstance(result.data, HealthStatus)
    assert result.data.name == "AgentName"
    assert result.data.status == "OK"
