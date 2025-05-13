from datetime import datetime
from unittest.mock import AsyncMock

import pytest
import ulid

from agentarena.controllers.model_controller import ModelController
from agentarena.factories.logger_factory import LoggingService
from agentarena.models.agent import AgentDTO
from agentarena.models.dbbase import DbBase
from agentarena.models.feature import FeatureDTO
from agentarena.models.strategy import StrategyDTO
from agentarena.models.strategy import StrategyType
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def mock_service():
    service = AsyncMock()
    return service


def fill_defaults(obj: DbBase):
    obj.id = ulid.ULID().hex
    obj.created_at = int(datetime.now().timestamp() - 1)


@pytest.mark.asyncio
async def test_create_success(mock_service, logging):
    feature_controller = ModelController[FeatureDTO](
        model_service=mock_service, logging=logging
    )
    # Arrange
    feature = FeatureDTO(
        name="Test Feature",
        description="A test feature",
        position="1,2",
        end_position=None,
        arena_config_id="arena123",
        origin="REQUIRED",
    )
    fresh = feature.model_copy()
    fill_defaults(fresh)
    mock_service.create.return_value = (fresh, ModelResponse(success=True))
    # Act
    result = await feature_controller.create_model(feature)
    # Assert
    assert result == fresh
    mock_service.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_success(mock_service, logging):
    stategy_controller = ModelController[StrategyDTO](
        model_service=mock_service, logging=logging
    )
    strategy = StrategyDTO(
        name="test strategy",
        personality="test",
        instructions="toast",
        description="testy",
        role=StrategyType.ANNOUNCER.value,
    )
    fresh = strategy.model_copy()
    fill_defaults(fresh)
    mock_service.update.return_value = (fresh, ModelResponse(success=True))
    # Act
    await stategy_controller.update_model("test", strategy)
    merged = strategy.model_copy()
    merged.id = "test"
    mock_service.update.assert_called_once_with(merged)


@pytest.mark.asyncio
async def test_delete_success(mock_service, logging):
    mock_service.delete.return_value = ModelResponse(success=True)
    agent_controller = ModelController[AgentDTO](
        model_service=mock_service, logging=logging
    )
    response = await agent_controller.delete_model("test")
    assert response["success"]
    mock_service.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_success(mock_service, logging):
    stategy_controller = ModelController[StrategyDTO](
        model_service=mock_service, logging=logging
    )
    strategy = StrategyDTO(
        name="test strategy",
        personality="test",
        instructions="toast",
        description="testy",
        role=StrategyType.ANNOUNCER.value,
    )
    fresh = strategy.model_copy()
    fill_defaults(fresh)
    mock_service.get.return_value = [fresh, ModelResponse(success=True)]
    retrieved = await stategy_controller.get_model("test")
    assert retrieved.id is not None
    assert retrieved.personality == "test"
