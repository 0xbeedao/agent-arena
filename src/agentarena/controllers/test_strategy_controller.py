from unittest.mock import AsyncMock

import pytest

from agentarena.controllers import strategy_controller
from agentarena.models.strategy import StrategyDTO
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def mock_strategy_service():
    service = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_create_strategy_success(mock_strategy_service):
    # Arrange
    strategy = StrategyDTO(
        id="strat1",
        name="Test Strategy",
        description="A test strategy",
        code="print('hi')",
        type="player",
        version="1.0",
    )
    mock_strategy_service.create.return_value = ["strat1", ModelResponse(success=True)]
    # Act
    result = await strategy_controller.create_strategy(
        strategy=strategy, strategy_service=mock_strategy_service
    )
    # Assert
    assert result == {"id": "strat1"}
    mock_strategy_service.create.assert_awaited_once()
