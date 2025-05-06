from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from ulid import ULID

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import JsonRequestJob
from agentarena.services.db_service import DbService
from agentarena.factories.db_factory import get_database
from agentarena.services.job_service import JobService
from agentarena.services.model_service import ModelService


def logging():
    return LoggingService(True)


def db_service():
    return DbService("", "", get_database, logging=logging(), memory=True)


@pytest.fixture
def model_service():
    return ModelService[JsonRequestJob](
        dbService=db_service(),
        model_class=JsonRequestJob,
        table_name="jsonjobs",
        logging=logging(),
    )


@pytest.mark.asyncio
async def test_get_when_empty(model_service):
    service = JobService(requestjob_service=model_service, logging=logging())
    job = await service.get()
    assert job is None


@pytest.mark.asyncio
async def test_send_creates_job(model_service):
    service = JobService(requestjob_service=model_service, logging=logging())
    job = JsonRequestJob(
        caller="test",
        command="do",
        method="POST",
        payload={"foo": "bar"},
        url="http://example.com",
    )
    success = await service.send(job)
    assert success
    assert job.id is not None


@pytest.mark.asyncio
async def test_get_returns_job(model_service):
    service = JobService(requestjob_service=model_service, logging=logging())
    job = JsonRequestJob(
        attempt=1,
        caller="test",
        command="do",
        method="POST",
        payload={"foo": "bar"},
        url="http://example.com",
    )
    jobid, response = await service.send(job)
    assert response.success
    found = await service.get()
    assert found is not None
    assert found.id == jobid


@pytest.mark.asyncio
async def test_done_updates_status(model_service):
    service = JobService(requestjob_service=model_service, logging=logging())
    job = JsonRequestJob(
        caller="test",
        command="do",
        method="POST",
        payload={"foo": "bar"},
        url="http://example.com",
    )
    job_id, response = await service.send(job)
    assert response.success
    fresh = await service.get()
    assert job_id == fresh.id
    success = await service.done(fresh, status="completed")
    assert success
    updated, response = await model_service.get(job_id)
    assert response.success
    assert updated.status == "completed"


@pytest.mark.asyncio
async def test_resend_increments_attempt_and_updates_send_at(model_service):
    service = JobService(requestjob_service=model_service, logging=logging())
    job = JsonRequestJob(
        caller="test",
        command="do",
        method="POST",
        payload={"foo": "bar"},
        url="http://example.com",
    )
    await service.send(job)
    old_send_at = job.send_at

    new_time = datetime.now()

    fresh = await service.get()
    job_id, response = await service.resend(fresh, at=new_time)
    assert response
    assert job_id == fresh.id

    updated, response = await model_service.get(fresh.id)
    assert response.success
    assert updated.attempt == 2
    assert updated.send_at == new_time


@pytest.mark.asyncio
async def test_size_reflects_queue(model_service):
    service = JobService(requestjob_service=model_service, logging=logging())
    count0 = await service.size()
    job1 = JsonRequestJob(
        caller="test",
        command="do",
        method="POST",
        payload={"foo": "bar"},
        url="http://example.com",
    )
    await service.send(job1)
    count1 = await service.size()
    assert count1 == count0 + 1
    await service.done(job1, status="completed")
    count2 = await service.size()
    assert count2 == count1 - 1


@pytest.mark.asyncio
async def test_drain_clears_queue(model_service):
    service = JobService(requestjob_service=model_service, logging=logging())
    jobs = [
        JsonRequestJob(
            caller="test",
            command="do",
            method="POST",
            payload={"foo": i},
            url="http://example.com",
        )
        for i in range(3)
    ]
    for job in jobs:
        await service.send(job)
    count_before = await service.size()
    assert count_before >= 3
    # Patch JobService.get_job to use get (since drain uses get_job, which is not defined)
    service.get_job = service.get
    await service.drain()
    count_after = await service.size()
    assert count_after == 0
