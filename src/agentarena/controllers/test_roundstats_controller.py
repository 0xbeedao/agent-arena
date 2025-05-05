from unittest.mock import AsyncMock

import pytest

from agentarena.controllers import roundstats_controller
from agentarena.models.stats import RoundStatsDTO
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def mock_roundstats_service():
    service = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_create_roundstats_success(mock_roundstats_service):
    # Arrange
    roundstats = RoundStatsDTO(
        id="rs1",
        arenastate_id="as-123",
        actions_count=1,
        duration_ms=100,
        metrics_json={},
    )
    mock_roundstats_service.create.return_value = ["rs1", ModelResponse(success=True)]
    # Act
    result = await roundstats_controller.create_roundstats(
        roundstats=roundstats, roundstats_service=mock_roundstats_service
    )
    # Assert
    assert result == {"id": "rs1"}
    mock_roundstats_service.create.assert_awaited_once()
