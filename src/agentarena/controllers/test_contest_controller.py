from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from agentarena.controllers.contest_controller import ContestController
from agentarena.factories.logger_factory import LoggingService
from agentarena.models.contest import ContestDTO
from agentarena.models.contest import ContestRequest
from agentarena.models.contest import ContestState
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def mock_contest_factory():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_contest_service():
    service = AsyncMock()
    return service


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.mark.asyncio
async def test_create_contest_success(
    mock_contest_service, mock_contest_factory, logging
):
    contest_controller = ContestController(
        model_service=mock_contest_service,
        contest_factory=mock_contest_factory,
        logging=logging,
    )
    # Arrange
    create_request = ContestRequest(
        arena_config_id="arena123", player_positions=["A", "B", "C", "D"]
    )
    contest_dto = ContestDTO(
        arena_config_id="arena123",
        current_round=1,
        player_positions="A;B;C;D",
        state=ContestState.CREATED.value,
        start_time=None,
        end_time=None,
        winner=None,
    )

    mock_contest_service.create.return_value = (
        contest_dto,
        ModelResponse(success=True),
    )
    # Act
    result = await contest_controller.create_contest(
        createRequest=create_request,
    )
    # Assert
    assert result == contest_dto
    mock_contest_service.create.assert_awaited_once()
