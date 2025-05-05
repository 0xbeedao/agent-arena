from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from agentarena.controllers import responder_controller
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus


@pytest.fixture
def mock_arenaagent_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_logging():
    logger = Mock()
    logger.get_logger.return_value = logger
    logger.info = Mock()
    return logger


@pytest.fixture
def mock_arenaagent_factory():
    factory = AsyncMock()
    return factory


@pytest.mark.asyncio
async def test_healthcheck_success(
    mock_arenaagent_service, mock_logging, mock_arenaagent_factory
):
    # Arrange
    arenaagent_id = "aa1"
    job_id = "job42"
    agent_dto = ArenaAgentDTO(
        arena_config_id="arena1", agent_id="agent1", role="player"
    )
    mock_arenaagent_service.get.return_value = (agent_dto, Mock(success=True))
    agent = Mock()
    agent.name = "AgentName"
    mock_arenaagent_factory.build.return_value = agent

    # Act
    result = await responder_controller.healthcheck(
        arenaagent_id=arenaagent_id,
        job_id=job_id,
        arenaagent_service=mock_arenaagent_service,
        logging=mock_logging,
        arenaagent_factory=mock_arenaagent_factory,
    )

    # Assert
    assert isinstance(result, HealthResponse)
    assert result.status == "completed"
    assert result.job_id == job_id
    assert isinstance(result.data, HealthStatus)
    assert result.data.name == "AgentName"
    assert result.data.status == "OK"
