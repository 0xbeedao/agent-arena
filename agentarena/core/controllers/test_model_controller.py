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
from agentarena.models.constants import PromptType
from agentarena.models.job import GenerateJob
from agentarena.models.job import GenerateJobCreate
from agentarena.models.public import GenerateJobPublic


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
    return ModelService[GenerateJob, GenerateJobCreate](
        model_class=GenerateJob,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def ctrl(model_service, logging):
    return ModelController[
        GenerateJob, GenerateJobCreate, GenerateJobCreate, GenerateJobPublic
    ](
        base_path="/api/generatejob",
        model_name="generatejob",
        model_create=GenerateJobCreate,
        model_update=GenerateJobCreate,
        model_public=GenerateJobPublic,
        model_service=model_service,
        logging=logging,
    )


@pytest.mark.asyncio
async def test_create_success(ctrl, db_service):
    with db_service.get_session() as session:
        # Arrange
        job = GenerateJobCreate(
            job_id="test_job_id",
            prompt_type=PromptType.ANNOUNCER_DESCRIBE_ARENA,
            model="test_model",
            prompt="test_prompt",
        )
        # Act
        result = await ctrl.create_model(job, session)
        # Assert
        assert result.id != ""


@pytest.mark.asyncio
async def test_delete_success(ctrl, db_service):
    with db_service.get_session() as session:
        job = GenerateJobCreate(
            job_id="test_job_id",
            prompt_type=PromptType.ANNOUNCER_DESCRIBE_ARENA,
            model="test_model",
            prompt="test_prompt",
        )
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
        job = GenerateJobCreate(
            job_id="test_job_id",
            prompt_type=PromptType.ANNOUNCER_DESCRIBE_ARENA,
            model="test_model",
            prompt="test_prompt",
        )
        result = await ctrl.create_model(job, session)
        retrieved = await ctrl.get_model(result.id, session)
        assert result.id == retrieved.id
        assert retrieved.model == job.model
        assert retrieved.prompt == job.prompt
        assert retrieved.prompt_type == job.prompt_type
