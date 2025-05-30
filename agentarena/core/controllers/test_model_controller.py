from unittest.mock import AsyncMock

import pytest
import ulid
from fastapi import HTTPException

from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
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
def message_broker():
    """Fixture to create a mock message broker"""
    broker = AsyncMock()
    broker.publish_model_change = AsyncMock()
    broker.publish_response = AsyncMock()
    return broker


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
def model_service(db_service, uuid_service, message_broker, logging):
    """Fixture to create a ModelService for features"""
    return ModelService[CommandJob, CommandJobCreate](
        model_class=CommandJob,
        message_broker=message_broker,
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
async def test_create_success(ctrl, db_service):
    with db_service.get_session() as session:
        # Arrange
        job = CommandJobCreate(id="", channel="test", method="GET", url="/test")
        # Act
        result = await ctrl.create_model(job, session)
        # Assert
        assert job.channel == result.channel
        assert result.id != ""


@pytest.mark.asyncio
async def test_update_success(ctrl, db_service):
    with db_service.get_session() as session:
        # Arrange
        job = CommandJobCreate(
            id="testing123", channel="test", method="GET", url="/test"
        )
        result = await ctrl.create_model(job, session)
        fid = result.id
        update = CommandJobUpdate(channel="foo")

        # Act
        updated = await ctrl.update_model(fid, update, session)
        assert updated.id == fid
        assert updated.method == "GET"
        assert updated.channel == "foo"


@pytest.mark.asyncio
async def test_delete_success(ctrl, db_service):
    with db_service.get_session() as session:
        job = CommandJobCreate(id="", channel="test", method="GET", url="/test")
        result = await ctrl.create_model(job, session)
        fid = result.id
        response = await ctrl.delete_model(fid, session)
        assert response["success"]
        try:
            await ctrl.get_model(fid, session)
            assert False, "should have failed"
        except HTTPException as e:
            pass


@pytest.mark.asyncio
async def test_get_success(ctrl, db_service):
    with db_service.get_session() as session:
        job = CommandJobCreate(channel="test", method="GET", url="/test")
        jid = ulid.ULID().hex
        job.id = jid
        result = await ctrl.create_model(job, session)
        retrieved = await ctrl.get_model(jid, session)
        assert result == retrieved
        assert retrieved.id == job.id
        assert retrieved.url == "/test"
