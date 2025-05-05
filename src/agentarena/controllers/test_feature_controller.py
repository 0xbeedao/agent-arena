from unittest.mock import AsyncMock

import pytest

from agentarena.controllers import feature_controller
from agentarena.models.feature import FeatureDTO
from agentarena.services.model_service import ModelResponse


@pytest.fixture
def mock_feature_service():
    service = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_create_feature_success(mock_feature_service):
    # Arrange
    feature = FeatureDTO(
        name="Test Feature",
        description="A test feature",
        position="1,2",
        end_position=None,
        arena_config_id="arena123",
        origin="REQUIRED",
    )
    mock_feature_service.create.return_value = [
        "feature789",
        ModelResponse(success=True),
    ]
    # Act
    result = await feature_controller.create_feature(
        feature=feature, feature_service=mock_feature_service
    )
    # Assert
    assert result == {"id": "feature789"}
    mock_feature_service.create.assert_awaited_once()
