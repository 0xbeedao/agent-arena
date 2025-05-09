import time
from datetime import datetime

import pytest

from agentarena.factories.db_factory import get_database
from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import JobState
from agentarena.models.job import JsonRequestJob
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def db_service():
    return DbService("", "", get_database, logging=LoggingService(True), memory=True)


def make_job_service(db_service, logging):
    return ModelService[JsonRequestJob](
        dbService=db_service,
        model_class=JsonRequestJob,
        table_name="jobs",
        logging=logging,
    )


@pytest.mark.asyncio
async def test_get_when_empty(db_service, logging):
    job_service = make_job_service(db_service, logging)
    q = QueueService(db_service=db_service, job_service=job_service, logging=logging)
    job = await q.get_next()
    assert job is None


@pytest.mark.asyncio
async def test_get(db_service, logging):
    job_service = make_job_service(db_service, logging)
    q = QueueService(db_service=db_service, job_service=job_service, logging=logging)
    job = JsonRequestJob(
        caller="test",
        command="test",
        method="GET",
        payload='{"test": "toast"}',
        url="/test",
    )
    next = await q.send_job(job)
    assert next is not None
    assert next.attempt == 1
    assert next.started_at == 0
    assert next.state == JobState.IDLE.value

    retrieved = await q.get_next()
    assert retrieved.id == next.id
    assert retrieved.state == JobState.REQUEST.value
    assert retrieved.started_at > 0


@pytest.mark.asyncio
async def test_get_unique(db_service, logging):
    job_service = make_job_service(db_service, logging)
    q = QueueService(db_service=db_service, job_service=job_service, logging=logging)
    job = JsonRequestJob(
        caller="testU",
        command="testX",
        method="GET",
        payload='{"testy": "toast"}',
        url="/test",
    )

    next = await q.send_job(job)
    assert next.started_at == 0

    live_job = await q.get_next()
    assert live_job.id == next.id
    assert live_job.started_at > datetime.now().timestamp() - 1000
    assert live_job.state == JobState.REQUEST.value

    no_job = await q.get_next()
    assert no_job is None


@pytest.mark.asyncio
async def test_update_state(db_service, logging):
    job_service = make_job_service(db_service, logging)
    q = QueueService(db_service=db_service, job_service=job_service, logging=logging)
    job = JsonRequestJob(
        caller="test",
        command="test",
        method="GET",
        payload='{"test": "toast"}',
        url="/test",
    )
    next = await q.send_job(job)
    assert next.started_at == 0

    live_job = await q.get_next()

    success = await q.update_state(live_job.id, JobState.COMPLETE.value, "test message")
    assert success

    dead_job, response = await q.job_service.get(live_job.id)
    assert response.success
    assert dead_job.state == JobState.COMPLETE.value
    assert dead_job.finished_at >= datetime.now().timestamp() - 1000
    assert dead_job.final_message == "test message"

    no_job = await q.get_next()
    assert no_job is None


@pytest.mark.asyncio
async def test_requeue_job(db_service, logging):
    job_service = make_job_service(db_service, logging)
    q = QueueService(db_service=db_service, job_service=job_service, logging=logging)
    # Create and send the original job
    job = JsonRequestJob(
        caller="test-requeue",
        command="requeue-test",
        method="POST",
        payload='{"foo": "bar"}',
        url="/requeue",
    )
    orig = await q.send_job(job)
    assert orig is not None
    orig_id = orig.id
    orig_attempt = orig.attempt

    # Mark the original job as complete so it's not in the queue
    await q.update_state(orig_id, JobState.COMPLETE.value, "finishing original")

    # Requeue the job
    requeued = await q.requeue_job(orig_id, eta=0)
    assert requeued is not None
    assert requeued.attempt == orig_attempt + 1
    assert getattr(requeued, "original_job", None) == orig_id
    assert requeued.state == JobState.IDLE.value
    assert (
        abs(datetime.now().timestamp() - requeued.send_at) < 5
    )  # should be approximately now
    assert requeued.id != orig_id

    time.sleep(1)
    # The requeued job should appear on the queue as next job
    picked = await q.get_next()
    assert picked is not None
    assert picked.id == requeued.id
    assert picked.attempt == requeued.attempt
