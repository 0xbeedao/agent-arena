from unittest.mock import AsyncMock

import pytest
import ulid

from agentarena.arena.models.arena import Feature
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelResponse, ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobCreate
from agentarena.models.job import CommandJobPublic
from agentarena.models.job import CommandJobUpdate


@pytest.fixture
def logging():
    return LoggingService(capture=True)


@pytest.fixture
def uuid_service(logging):
    return UUIDService(word_list=[], prod=False)


@pytest.fixture
def db_service(uuid_service, logging):
    """Fixture to create an in-memory DB service"""
    service = DbService(
        str(get_project_root()),
        dbfile="test.db",
        get_engine=get_engine,
        memory=True,
        prod=False,
        uuid_service=uuid_service,
        logging=logging,
    )
    return service.create_db()


@pytest.fixture
def model_service(db_service, uuid_service, logging):
    """Fixture to create a ModelService for features"""
    return ModelService[Feature](
        model_class=Feature,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def ctrl(model_service, logging):
    return ModelController[
        CommandJob, CommandJobCreate, CommandJobUpdate, CommandJobPublic
    ](model_public=CommandJobPublic, model_service=model_service, logging=logging)


@pytest.mark.asyncio
async def test_create_success(ctrl, model_service):
    # Arrange
    job = CommandJobCreate(channel="test", method="GET", url="/test")
    # Act
    result = await ctrl.create_model(job)
    # Assert
    assert job.channel == result.channel
    assert result.id


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
