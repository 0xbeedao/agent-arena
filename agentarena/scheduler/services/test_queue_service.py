import time
from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobCreate
from agentarena.models.job import CommandJobHistory
from agentarena.models.job import JobState
from agentarena.models.job import UrlJobRequest
from agentarena.scheduler.services.queue_service import QueueService


@pytest.fixture
def mock_nats_client():
    client = AsyncMock()
    client.publish = AsyncMock()
    return client


@pytest.fixture
def logging():
    return LoggingService(capture=True)


@pytest.fixture
def uuid_service():
    return UUIDService(word_list=[])


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
def job_service(db_service, uuid_service, message_broker, logging):
    return ModelService[CommandJob, CommandJobCreate](
        db_service=db_service,
        model_class=CommandJob,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def history_service(db_service, uuid_service, message_broker, logging):
    return ModelService[CommandJobHistory, CommandJobHistory](
        db_service=db_service,
        model_class=CommandJobHistory,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )


@pytest.fixture
def message_broker(mock_nats_client, uuid_service, logging):
    broker = MessageBroker(
        client=mock_nats_client,
        uuid_service=uuid_service,
        logging=logging,
    )
    return broker


@pytest.fixture
def q(job_service, history_service, message_broker, logging):
    return QueueService(
        history_service=history_service,
        message_broker=message_broker,
        job_service=job_service,
        logging=logging,
    )


@pytest.mark.asyncio
async def test_get_when_empty(q, db_service):
    with db_service.get_session() as session:
        job = await q.get_next(session)
        assert job is None


@pytest.mark.asyncio
async def test_get(q, db_service):
    job = CommandJob(
        id="testget",
        channel="job.request.url",
        method="GET",
        data='{"test": "toast"}',
        url="/test",
    )
    with db_service.get_session() as session:
        next = await q.add_job(job, session)
        assert next is not None
        assert next.started_at == 0
        assert next.state == JobState.IDLE

        retrieved = await q.get_next(session)
        assert retrieved is not None
        assert retrieved.id == next.id
        assert retrieved.state == JobState.REQUEST
        assert retrieved.started_at > 0


@pytest.mark.asyncio
async def test_get_unique(q, db_service):
    job = CommandJob(
        id="test",
        channel="job.request.url",
        method="GET",
        data={"testy": "toast"},
        url="/test",
    )

    with db_service.get_session() as session:
        next = await q.add_job(job, session)
        assert next is not None
        assert next.started_at == 0

        live_job = await q.get_next(session)
        assert live_job is not None
        assert live_job.id == next.id
        assert live_job.started_at > datetime.now().timestamp() - 1000
        assert live_job.state == JobState.REQUEST

        no_job = await q.get_next(session)
        assert no_job is None


@pytest.mark.asyncio
async def test_update_state(q, db_service, message_broker, mock_nats_client):
    job = CommandJob(
        id="test",
        channel="job.request.url",
        method="GET",
        data={"test": "toast"},
        url="/test",
    )
    with db_service.get_session() as session:
        next = await q.add_job(job, session)
        assert next is not None
        assert next.started_at == 0

        live_job = await q.get_next(session)
        assert live_job is not None
        job_id = live_job.id

        updated = await q.update_state(
            job_id, JobState.COMPLETE, session, message="test message"
        )
        assert updated

        # should send final message
        mock_nats_client.publish.assert_awaited()

        job = session.get(CommandJob, job_id)
        assert job

        # check children
        histories = [h for h in job.history]
        assert histories
        last = histories.pop()
        assert last is not None
        assert last.message == "test message"

        assert job.parent is None

        no_job = await q.get_next(session)
        assert no_job is None


@pytest.mark.asyncio
async def test_requeue_job(q, db_service):
    job = CommandJob(
        id="testrequeue",
        channel="job.request.url",
        method="POST",
        data={"foo": "bar"},
        url="/requeue",
    )
    with db_service.get_session() as session:
        orig = await q.add_job(job, session)
        assert orig is not None
        orig_id = orig.id

        # Mark the original job as complete so it's not in the queue
        await q.update_state(
            orig_id, JobState.COMPLETE, session, message="finishing original"
        )

        # Requeue the job
        requeued = await q.requeue_job(orig_id, session, delay=0)
        assert requeued is not None
        assert requeued.state == JobState.IDLE
        assert (
            abs(datetime.now().timestamp() - requeued.send_at) < 5
        )  # should be approximately now
        assert requeued.id == orig_id

        time.sleep(1)
        # The requeued job should appear on the queue as next job
        picked = await q.get_next(session)
        assert picked is not None
        assert picked.id == requeued.id


@pytest.mark.asyncio
async def test_get_idle_batch(q, db_service):
    job = CommandJob(
        id="idlebatch",
        channel="test.request.batch",
        method="MESSAGE",
        data={"test": "toast"},
        url="/test",
    )
    with db_service.get_session() as session:
        next = await q.add_job(job, session)
        assert next is not None
        assert next.started_at == 0
        assert next.state == JobState.IDLE

        retrieved = await q.get_next(session)
        assert retrieved is not None
        assert retrieved.id == next.id
        assert retrieved.state == JobState.REQUEST
        assert retrieved.started_at > 0


@pytest.mark.asyncio
async def test_batch_state_updates(q, db_service, job_service):
    # Create a batch job
    batch_req = CommandJobCreate(
        channel="test.batch.request",
        method="MESSAGE",
        data='{"batch": "data"}',
        state=JobState.REQUEST,
        url="/batch",
    )

    # Create request summaries for child jobs
    requests = [
        UrlJobRequest(
            method="GET",
            url="/request1",
            data='{"req": "1"}',
        ),
        UrlJobRequest(
            method="GET",
            url="/request2",
            data='{"req": "2"}',
        ),
    ]

    batch_id = ""
    child_ids = []
    children = []

    with db_service.get_session() as session:
        batch = await q.add_job(batch_req, session)
        assert batch is not None
        batch_id = batch.id
        for r in requests:
            child = batch.make_child(r)
            child_job = await q.add_job(child, session)
            assert child_job is not None
            child_ids.append(child_job.id)

        session.commit()

        fresh = session.get(CommandJob, batch_id)
        assert fresh

        for cid in child_ids:
            child = session.get(CommandJob, cid)
            assert child
            assert child.parent == fresh
            children.append(child)

        # Process first child job
        child1 = children[0]
        await q.update_state(child1.id, JobState.COMPLETE, session, "Child 1 complete")

        # Batch should still be in REQUEST state since one child is pending
        session.refresh(batch)
        assert batch.state == JobState.REQUEST

        # Process second child job
        child2 = children[1]
        await q.update_state(child2.id, JobState.COMPLETE, session, "Child 2 complete")

        # Now batch should be IDLE since all children are complete
        session.commit()
        session.refresh(batch)
        assert batch.state == JobState.IDLE

        # check that we get the batch to process now
        batch_check = await q.get_next(session)
        assert batch_check is not None
        assert batch_check.id == batch.id
        assert batch_check.url == batch.url
        assert batch_check.state == JobState.REQUEST


@pytest.mark.asyncio
async def test_batch_with_failed_child(
    q, job_service, db_service
):  # Create a batch job
    batch_req = CommandJobCreate(
        channel="test.batch.fail",
        method="POST",
        url="/batch",
        data={},
        state=JobState.REQUEST,
    )

    # Create request summaries for child jobs
    requests = [
        UrlJobRequest(method="GET", url="/request1", data=None),
        UrlJobRequest(method="GET", url="/request2", data=None),
    ]

    batch_id = ""
    child_ids = []
    children = []

    with db_service.get_session() as session:
        batch = await q.add_job(batch_req, session)
        assert batch is not None
        batch_id = batch.id
        for r in requests:
            child = batch.make_child(r)
            child_job = await q.add_job(child, session)
            assert child_job is not None
            child_ids.append(child_job.id)

        session.commit()

        fresh = session.get(CommandJob, batch_id)
        assert fresh

        for cid in child_ids:
            child = session.get(CommandJob, cid)
            assert child
            assert child.parent == fresh
            children.append(child)

        # Complete first child job successfully
        child1 = children[0]
        await q.update_state(child1.id, JobState.COMPLETE, session, "Child 1 complete")

        # Fail the second child job
        child2 = children[1]
        await q.update_state(child2.id, JobState.FAIL, session, "Child 2 failed")

        # Batch should be in FAIL state since one child failed
        session.commit()
        session.refresh(batch)
        assert batch.state == JobState.FAIL


@pytest.mark.asyncio
async def test_batch_send_1(q, db_service):
    batch_req = CommandJobCreate(
        channel="test.batch",
        method="GET",
        data={"test": "toast"},
        url="/test",
        state=JobState.REQUEST,
    )
    requests = [UrlJobRequest(url="/test/1", method="GET", data={}, delay=0)]

    batch_id = ""
    child_ids = []
    children = []

    with db_service.get_session() as session:
        batch = await q.add_job(batch_req, session)
        assert batch is not None
        batch_id = batch.id
        for r in requests:
            child = batch.make_child(r)
            child_job = await q.add_job(child, session)
            assert child_job is not None
            child_ids.append(child_job.id)

        session.commit()

        fresh = session.get(CommandJob, batch_id)
        assert fresh

        for cid in child_ids:
            child = session.get(CommandJob, cid)
            assert child
            assert child.parent == fresh
            children.append(child)

        assert batch.started_at == 0
        assert batch.state == JobState.REQUEST

        child = await q.get_next(session)
        assert child is not None
        assert child.id != batch.id
        assert child.parent_id == batch.id
        assert child.url == "/test/1"
        assert child.state == JobState.REQUEST
        assert child.started_at > 0

        # child is in request, batch is in request - nothing in q
        should_be_empty = await q.get_next(session)
        assert should_be_empty is None

        # complete the child, should trigger parent updates
        updated = await q.update_state(
            child.id, JobState.COMPLETE, session, message="success"
        )
        assert updated is not None
        assert updated.id == child.id

        # parent should now be idle, and ready to get picket up from q

        ready_batch = await q.get_next(session)
        assert ready_batch is not None
        assert ready_batch.id == batch.id
        assert ready_batch.state == JobState.REQUEST
