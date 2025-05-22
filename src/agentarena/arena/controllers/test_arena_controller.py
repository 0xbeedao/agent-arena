from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from agentarena.arena.controllers.arena_controller import ArenaController
from agentarena.arena.models.arena import ArenaCreate
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelResponse


@pytest.fixture
def mock_arena_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_agent_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_feature_service():
    service = AsyncMock()
    return service


@pytest.fixture
def logging():
    return LoggingService(True)


class ArenaStub(BaseModel):
    name: str
    id: str


@pytest.mark.asyncio
async def test_create_arena_success(
    mock_arena_service,
    mock_agent_service,
    logging,
    mock_feature_service,
):
    arena_controller = ArenaController(
        arena_service=mock_arena_service,
        feature_service=mock_feature_service,
        logging=logging,
    )
    # Arrange
    create_request = ArenaCreate(
        name="Test Arena",
        description="A test arena",
        height=10,
        width=10,
        rules="No rules",
        max_random_features=0,
        winning_condition="score",
        features=[],
    )

    mock_arena = ArenaStub(name="test", id="testid")

    mock_arena_service.create.return_value = [mock_arena, ModelResponse(success=True)]
    mock_feature_service.validate_list.return_value = []
    mock_agent_service.get_by_ids.return_value = [[], []]
    # Act
    result = await arena_controller.create_arena(create_request)
    # Assert
    assert result == mock_arena
    mock_arena_service.create.assert_awaited_once()


# Additional tests for error cases, get_arena, get_arena_list, update_arena, delete_arena, etc. should be added similarly.
