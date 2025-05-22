from unittest.mock import AsyncMock
from unittest.mock import Mock

import pytest

from agentarena.arena.controllers.contest_controller import ContestController
from agentarena.arena.models.arena import Contest
from agentarena.arena.models.arena import ContestCreate
from agentarena.arena.models.arena import ContestState
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelResponse


@pytest.fixture
def mock_contest_factory():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_contest_service():
    service = AsyncMock()
    return service


@pytest.fixture
def mock_participant_service():
    service = AsyncMock()
    return service


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.mark.asyncio
async def test_create_contest_success(
    mock_contest_service, mock_participant_service, logging
):
    contest_controller = ContestController(
        model_service=mock_contest_service,
        participant_service=mock_participant_service,
        logging=logging,
    )
    mock_participant_service.get.return_value = (Mock(), None)
    # Arrange
    create_request = ContestCreate(
        arena_id="arena123",
        player_positions="A;B;C;D",
        participant_ids=["a", "b", "c"],
    )
    contest = Contest(
        arena_id="arena123",
        current_round=1,
        player_positions="A;B;C;D",
        state=ContestState.CREATED.value,
        start_time=None,
        end_time=None,
    )

    mock_contest_service.create.return_value = (
        contest,
        ModelResponse(success=True),
    )
    # Act
    result = await contest_controller.create_contest(
        create_request,
    )
    # Assert
    assert result == contest
    mock_contest_service.create.assert_awaited_once()
