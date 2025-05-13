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
from agentarena.models.job import JsonRequestSummary
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService
from agentarena.services.uuid_service import UUIDService


@pytest.fixture
def logging():
    return LoggingService(True)


def uuid_service():
    return UUIDService(word_list=None)


@pytest.fixture
def db_service():
    return DbService(
        "",
        "",
        get_database,
        logging=LoggingService(True),
        uuid_service=uuid_service(),
        memory=True,
    )


@pytest.fixture
def job_service(db_service, logging):
    return ModelService[CommandJob](
        db_service=db_service,
        model_class=CommandJob,
        table_name="jobs",
        logging=logging,
    )


@pytest.fixture
def history_service(db_service, logging):
    return ModelService[CommandJobHistory](
        db_service=db_service,
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


@pytest.mark.asyncio
async def test_send_batch(job_service, history_service, event_bus, logging):
    q = QueueService(
        history_service=history_service,
        event_bus=event_bus,
        job_service=job_service,
        logging=logging,
    )
    # Create a batch job
    batch_job = CommandJob(
        command=JobCommandType.BATCH.value,
        method="POST",
        data='{"batch": "data"}',
        url="/batch",
    )

    # Create request summaries for child jobs
    requests = [
        JsonRequestSummary(
            method="GET",
            url="/request1",
            data='{"req": "1"}',
        ),
        JsonRequestSummary(
            method="GET",
            url="/request2",
            data='{"req": "2"}',
        ),
    ]

    # Send the batch with child requests
    result = await q.send_batch(batch_job, requests)
    assert result is not None
    assert result.command == JobCommandType.BATCH.value
    assert result.state == JobState.REQUEST.value

    # Get the child jobs
    batch_id = result.id
    children = await job_service.get_where("parent_id = :pid", {"pid": batch_id})
    assert len(children) == 2

    # Verify child jobs are correctly created
    for child in children:
        assert child.parent_id == batch_id
        assert child.command == JobCommandType.REQUEST.value
        assert child.state == JobState.IDLE.value


@pytest.mark.asyncio
async def test_batch_state_updates(job_service, history_service, event_bus, logging):
    q = QueueService(
        history_service=history_service,
        event_bus=event_bus,
        job_service=job_service,
        logging=logging,
    )
    # Create a batch job
    batch_job = CommandJob(
        command=JobCommandType.BATCH.value,
        method="POST",
        data='{"batch": "data"}',
        url="/batch",
    )

    # Create request summaries for child jobs
    requests = [
        JsonRequestSummary(
            method="GET",
            url="/request1",
            data='{"req": "1"}',
        ),
        JsonRequestSummary(
            method="GET",
            url="/request2",
            data='{"req": "2"}',
        ),
    ]

    # Send the batch with child requests
    batch = await q.send_batch(batch_job, requests)
    batch_id = batch.id

    # Get the child jobs
    children = await job_service.get_where("parent_id = :pid", {"pid": batch_id})
    assert len(children) == 2

    # Process first child job
    child1 = children[0]
    await q.update_state(child1.id, JobState.COMPLETE.value, "Child 1 complete")

    # Batch should still be in REQUEST state since one child is pending
    batch_updated, _ = await job_service.get(batch_id)
    assert batch_updated.state == JobState.REQUEST.value

    # Process second child job
    child2 = children[1]
    await q.update_state(child2.id, JobState.COMPLETE.value, "Child 2 complete")

    # Now batch should be COMPLETE since all children are complete
    batch_final, _ = await job_service.get(batch_id)
    assert batch_final.state == JobState.COMPLETE.value


@pytest.mark.asyncio
async def test_batch_with_failed_child(
    job_service, history_service, event_bus, logging
):
    q = QueueService(
        history_service=history_service,
        event_bus=event_bus,
        job_service=job_service,
        logging=logging,
    )
    # Create a batch job
    batch_job = CommandJob(
        command=JobCommandType.BATCH.value, method="POST", url="/batch", data=""
    )

    # Create request summaries for child jobs
    requests = [
        JsonRequestSummary(method="GET", url="/request1", data=""),
        JsonRequestSummary(method="GET", url="/request2", data=""),
    ]

    # Send the batch with child requests
    batch = await q.send_batch(batch_job, requests)
    batch_id = batch.id

    # Get the child jobs
    children = await job_service.get_where("parent_id = :pid", {"pid": batch_id})

    # Complete first child job successfully
    child1 = children[0]
    await q.update_state(child1.id, JobState.COMPLETE.value, "Child 1 complete")

    # Fail the second child job
    child2 = children[1]
    await q.update_state(child2.id, JobState.FAIL.value, "Child 2 failed")

    # Batch should be in FAIL state since one child failed
    batch_final, _ = await job_service.get(batch_id)
    assert batch_final.state == JobState.FAIL.value
