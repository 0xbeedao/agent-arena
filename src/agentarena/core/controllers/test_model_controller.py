from datetime import datetime
from unittest.mock import AsyncMock

import pytest
import ulid

from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelResponse
from agentarena.models.dbbase import DbBase
from agentarena.models.job import (
    CommandJob,
    CommandJobCreate,
    CommandJobPublic,
    CommandJobUpdate,
)


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def mock_service():
    service = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_create_success(mock_service, logging):
    ctrl = ModelController[
        CommandJob, CommandJobCreate, CommandJobUpdate, CommandJobPublic
    ](model_public=CommandJobPublic, model_service=mock_service, logging=logging)
    # Arrange
    job = CommandJobCreate(channel="test", method="GET", url="/test")
    fresh = job.model_copy()
    mock_service.create.return_value = (job, ModelResponse(success=True))
    # Act
    result = await ctrl.create_model(job)
    # Assert
    assert job == fresh
    mock_service.create.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_success(mock_service, logging):
    ctrl = ModelController[
        CommandJob, CommandJobCreate, CommandJobUpdate, CommandJobPublic
    ](model_public=CommandJobPublic, model_service=mock_service, logging=logging)
    # Arrange
    job = CommandJobUpdate(channel="foo", method="GET")
    fresh = job.model_dump()
    fresh["id"] = ulid.ULID().hex
    mock_service.update.return_value = (fresh, ModelResponse(success=True))
    # Act
    await ctrl.update_model(fresh["id"], job)
    mock_service.update.assert_called_once_with(fresh["id"], job)


@pytest.mark.asyncio
async def test_delete_success(mock_service, logging):
    mock_service.delete.return_value = ModelResponse(success=True)
    ctrl = ModelController[
        CommandJob, CommandJobCreate, CommandJobUpdate, CommandJobPublic
    ](model_public=CommandJobPublic, model_service=mock_service, logging=logging)

    response = await ctrl.delete_model("test")
    assert response["success"]
    mock_service.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_success(mock_service, logging):
    ctrl = ModelController[
        CommandJob, CommandJobCreate, CommandJobUpdate, CommandJobPublic
    ](model_public=CommandJobPublic, model_service=mock_service, logging=logging)
    job = CommandJob(channel="test", method="GET", url="/test")
    jid = ulid.ULID().hex
    job.id = jid
    mock_service.get.return_value = [job, ModelResponse(success=True)]
    retrieved = await ctrl.get_model("test")
    assert retrieved.id == job.id
    assert retrieved.url == "/test"
    mock_service.get.assert_awaited_once()
