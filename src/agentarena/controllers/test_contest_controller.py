from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from agentarena.controllers import contest_controller
from agentarena.models.contest import ContestDTO
from agentarena.models.contest import ContestRequest
from agentarena.models.contest import ContestStatus
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def mock_contest_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_make_arenaagent():
    async def dummy_make_arenaagent(dto):
        return Mock()

    return dummy_make_arenaagent


@pytest.mark.asyncio
async def test_create_contest_success(mock_contest_service, mock_make_arenaagent):
    # Arrange
    create_request = ContestRequest(
        arena_config_id="arena123", player_positions=["A", "B", "C", "D"]
    )
    contest_dto = ContestDTO(
        arena_config_id="arena123",
        current_round=1,
        player_positions="A;B;C;D",
        status=ContestStatus.CREATED.value,
        start_time=None,
        end_time=None,
        winner=None,
    )
    mock_contest_service.create.return_value = [
        "contest456",
        ModelResponse(success=True),
    ]
    # Act
    result = await contest_controller.create_contest(
        createRequest=create_request,
        contest_service=mock_contest_service,
        make_arenaagent=mock_make_arenaagent,
    )
    # Assert
    assert result == {"id": "contest456"}
    mock_contest_service.create.assert_awaited_once()
