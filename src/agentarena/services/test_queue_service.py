import time
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agentarena.factories.db_factory import get_database
from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobHistory
from agentarena.models.job import JobCommandType
from agentarena.models.job import JobState
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def db_service():
    return DbService("", "", get_database, logging=LoggingService(True), memory=True)


@pytest.fixture
def job_service(db_service, logging):
    return ModelService[CommandJob](
        dbService=db_service,
        model_class=CommandJob,
        table_name="jobs",
        logging=logging,
    )


@pytest.fixture
def history_service(db_service, logging):
    return ModelService[CommandJobHistory](
        dbService=db_service,
        model_class=CommandJobHistory,
        table_name="jobhistory",
        logging=logging,
    )


@pytest.fixture
def event_bus():
    service = AsyncMock()
    return service


@pytest.mark.asyncio
async def test_get_when_empty(job_service, logging):
    q = QueueService(
        event_bus=None,
        history_service=None,
        job_service=job_service,
        logging=logging,
    )
    job = await q.get_next()
    assert job is None


@pytest.mark.asyncio
async def test_get(job_service, history_service, event_bus, logging):
    q = QueueService(
        history_service=history_service,
        event_bus=event_bus,
        job_service=job_service,
        logging=logging,
    )
    job = CommandJob(
        command=JobCommandType.REQUEST.value,
        method="GET",
        data='{"test": "toast"}',
        url="/test",
    )
    next = await q.send_job(job)
    assert next is not None
    assert next.started_at == 0
    assert next.state == JobState.IDLE.value

    retrieved = await q.get_next()
    assert retrieved.id == next.id
    assert retrieved.state == JobState.REQUEST.value
    assert retrieved.started_at > 0


@pytest.mark.asyncio
async def test_get_unique(job_service, history_service, event_bus, logging):
    q = QueueService(
        history_service=history_service,
        event_bus=event_bus,
        job_service=job_service,
        logging=logging,
    )
    job = CommandJob(
        command=JobCommandType.REQUEST.value,
        method="GET",
        data='{"testy": "toast"}',
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
async def test_update_state(job_service, history_service, event_bus, logging):
    q = QueueService(
        history_service=history_service,
        event_bus=event_bus,
        job_service=job_service,
        logging=logging,
    )
    job = CommandJob(
        command=JobCommandType.REQUEST.value,
        method="GET",
        data='{"test": "toast"}',
        url="/test",
    )
    next = await q.send_job(job)
    assert next.started_at == 0

    live_job = await q.get_next()

    job_id = live_job.id

    success = await q.update_state(job_id, JobState.COMPLETE.value, "test message")
    assert success

    dead_job, response = await q.job_service.get(job_id)
    assert response.success
    assert dead_job.state == JobState.COMPLETE.value
    assert dead_job.finished_at >= datetime.now().timestamp() - 1000

    histories = await q.history_service.get_where(
        "job_id=:jid", {"jid": job_id}, order_by="created_at desc"
    )
    rows = [h for h in histories]
    last = rows.pop()
    assert last is not None
    assert last.message == "test message"

    # assert dead_job.final_message == "test message"

    no_job = await q.get_next()
    assert no_job is None


@pytest.mark.asyncio
async def test_requeue_job(job_service, history_service, event_bus, logging):
    q = QueueService(
        history_service=history_service,
        event_bus=event_bus,
        job_service=job_service,
        logging=logging,
    )
    job = CommandJob(
        command=JobCommandType.REQUEST.value,
        method="POST",
        data='{"foo": "bar"}',
        url="/requeue",
    )
    orig = await q.send_job(job)
    assert orig is not None
    orig_id = orig.id

    # Mark the original job as complete so it's not in the queue
    await q.update_state(orig_id, JobState.COMPLETE.value, "finishing original")

    # Requeue the job
    requeued = await q.requeue_job(orig_id, delay=0)
    assert requeued is not None
    assert requeued.state == JobState.IDLE.value
    assert (
        abs(datetime.now().timestamp() - requeued.send_at) < 5
    )  # should be approximately now
    assert requeued.id == orig_id

    time.sleep(1)
    # The requeued job should appear on the queue as next job
    picked = await q.get_next()
    assert picked is not None
    assert picked.id == requeued.id
