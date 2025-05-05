from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from agentarena.controllers import arena_controller
from agentarena.models.arena import ArenaCreateRequest
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def mock_arena_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_agent_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_logger():
    logger = Mock()
    logger.get_logger.return_value = logger
    logger.info = Mock()
    logger.debug = Mock()
    logger.error = Mock()
    logger.bind = Mock(return_value=logger)
    return logger


@pytest.mark.asyncio
async def test_create_arena_success(
    mock_arena_service, mock_agent_service, mock_logger
):
    # Arrange
    create_request = ArenaCreateRequest(
        name="Test Arena",
        description="A test arena",
        height=10,
        width=10,
        rules="No rules",
        max_random_features=0,
        winning_condition="score",
        features=[],
        agents=[],
    )
    mock_arena_service.create.return_value = ["arena123", ModelResponse(success=True)]
    mock_agent_service.get_by_ids.return_value = ([], [])
    # Act
    result = await arena_controller.create_arena(
        createRequest=create_request,
        arena_service=mock_arena_service,
        agent_service=mock_agent_service,
        logging=mock_logger,
    )
    # Assert
    assert result == {"id": "arena123"}
    mock_arena_service.create.assert_awaited_once()
    mock_logger.get_logger.assert_called_with(
        module="arena_controller", endpoint="create_arena"
    )


# Additional tests for error cases, get_arena, get_arena_list, update_arena, delete_arena, etc. should be added similarly.
