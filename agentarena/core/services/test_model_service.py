from datetime import datetime
from typing import Dict
from unittest.mock import AsyncMock

import pytest

from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobCreate
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
    """Fixture to create a ModelService for CommandJob"""
    return ModelService[CommandJob, CommandJobCreate](
        model_class=CommandJob,
        message_broker=message_broker,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def sample_job_data() -> Dict:
    """Sample job data for testing"""
    return {
        "channel": "test.channel",
        "url": "http://example.com",
        "method": "GET",
        "priority": 5,
        "send_at": int(datetime.now().timestamp()),
        "state": "idle",
    }


@pytest.mark.asyncio
async def test_create_job(
    model_service: ModelService[CommandJob, CommandJobCreate], sample_job_data: Dict
):
    """Test creating a job"""
    job_create = CommandJobCreate(**sample_job_data)
    with model_service.get_session() as session:
        created_job, response = await model_service.create(job_create, session)

        assert created_job is not None
        assert response is not None
        assert response.success is True
        assert created_job.id is not None
        assert created_job.channel == sample_job_data["channel"]


@pytest.mark.asyncio
async def test_get_job(
    model_service: ModelService[CommandJob, CommandJobCreate], sample_job_data: Dict
):
    """Test getting a job by ID"""
    job_create = CommandJobCreate(**sample_job_data)
    with model_service.get_session() as session:
        created_job, _ = await model_service.create(job_create, session)

        assert created_job is not None
        retrieved_job, response = await model_service.get(created_job.id, session)

        assert retrieved_job is not None
        assert response.success is True
        assert retrieved_job.id == created_job.id
        assert retrieved_job.channel == created_job.channel


@pytest.mark.asyncio
async def test_update_job(
    model_service: ModelService[CommandJob, CommandJobCreate], sample_job_data: Dict
):
    """Test updating a job"""
    job_create = CommandJobCreate(**sample_job_data)
    with model_service.get_session() as session:
        created_job, _ = await model_service.create(job_create, session)
        assert created_job is not None

        update_data = {
            "state": "complete",
            "finished_at": int(datetime.now().timestamp()),
        }
        job_update = CommandJobUpdate(**update_data)

        updated_job, response = await model_service.update(
            created_job.id, job_update, session
        )

        assert updated_job is not None
        assert response.success is True
        assert updated_job.state == "complete"
        assert updated_job.finished_at > 0


@pytest.mark.asyncio
async def test_delete_job(
    model_service: ModelService[CommandJob, CommandJobCreate], sample_job_data: Dict
):
    """Test deleting a job"""
    job_create = CommandJobCreate(**sample_job_data)
    with model_service.get_session() as session:
        created_job, _ = await model_service.create(job_create, session)

        assert created_job is not None
        response = await model_service.delete(created_job.id, session)

        assert response.success is True

        # Verify job is actually deleted
        deleted_job, get_response = await model_service.get(created_job.id, session)
        assert deleted_job is None
        assert get_response.success is False


@pytest.mark.asyncio
async def test_list_jobs(
    model_service: ModelService[CommandJob, CommandJobCreate], sample_job_data: Dict
):
    """Test listing jobs"""
    # Create 3 jobs
    with model_service.get_session() as session:
        for i in range(3):
            data = sample_job_data.copy()
            data["channel"] = f"channel.{i}"
            job_create = CommandJobCreate(**data)
            await model_service.create(job_create, session)

        jobs = await model_service.list(session)
        work = [j for j in jobs]
        assert len(work) == 3
        assert all(isinstance(job, CommandJob) for job in work)
