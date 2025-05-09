from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel

from agentarena.controllers.arena_controller import ArenaController
from agentarena.factories.logger_factory import LoggingService
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
def mock_feature_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_arena_factory():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_participant_service():
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
    mock_participant_service,
    mock_arena_factory,
):
    arena_controller = ArenaController(
        agent_service=mock_agent_service,
        model_service=mock_arena_service,
        feature_service=mock_feature_service,
        participant_service=mock_participant_service,
        arena_factory=mock_arena_factory,
        logging=logging,
    )
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

    mock_arena = ArenaStub(name="test", id="testid")

    mock_result_arena = ArenaStub(name="test", id="testid")

    mock_arena_service.create.return_value = [mock_arena, ModelResponse(success=True)]
    mock_arena_factory.build.return_value = mock_result_arena
    mock_agent_service.get_by_ids.return_value = [[], []]
    # Act
    result = await arena_controller.create_arena(
        createRequest=create_request,
    )
    # Assert
    assert result == mock_result_arena
    mock_arena_service.create.assert_awaited_once()


# Additional tests for error cases, get_arena, get_arena_list, update_arena, delete_arena, etc. should be added similarly.
