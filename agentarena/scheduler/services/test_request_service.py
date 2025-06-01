from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import CommandJob
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.scheduler.services.request_service import RequestService


def make_job(name: str):
    return CommandJob(
        id=name,
        channel="test.command",
        method="GET",
        data={"test": 1},
        finished_at=0,
        send_at=0,
        state=JobState.IDLE,
        started_at=int(datetime.now().timestamp()),
        url=f"http://localhost:8000/{name}",
    )


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def queue_service():
    service = AsyncMock()
    return service


@pytest.fixture
def message_broker():
    service = AsyncMock()
    return service


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
def svc(message_broker, queue_service, logging):
    svc = RequestService(
        actor_url="http://localhost:8000",
        arena_url="http://localhost:8000",
        queue_service=queue_service,
        message_broker=message_broker,
        logging=logging,
    )
    return svc


def make_success_response() -> JobResponse:
    return JobResponse(
        job_id="test-response",
        state=JobResponseState.COMPLETE,
        data={"check": "yep"},
        url="/test",
    )


def make_pending_response() -> JobResponse:
    return JobResponse(
        job_id="test-response",
        state=JobResponseState.PENDING,
        delay=1,
        url="/nope",
    )


@pytest.mark.asyncio
async def test_no_jobs(svc, queue_service, db_service):
    with db_service.get_session() as session:
        queue_service.get_next.return_value = None
        response = await svc.poll_and_process(session)
        assert response is False
        queue_service.get_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_job_success(queue_service, svc, httpx_mock, db_service):
    with db_service.get_session() as session:
        job = make_job("xxx")
        queue_service.get_next.return_value = job
        queue_service.update_state.return_value = make_job("xxx")

        job_response = make_success_response()
        httpx_mock.add_response(
            status_code=200,
            method="GET",
            url="http://localhost:8000/xxx",
            content=job_response.model_dump_json(),
        )

        success = await svc.poll_and_process(session)
        assert success


@pytest.mark.asyncio
async def test_poll_job_pending(queue_service, svc, httpx_mock, db_service):
    with db_service.get_session() as session:
        job = make_job("xxx")
        queue_service.get_next.return_value = job
        queue_service.requeue_job.return_value = make_job("yyy")

        job_response = make_pending_response()
        httpx_mock.add_response(
            status_code=200,
            method="GET",
            url="http://localhost:8000/xxx",
            content=job_response.model_dump_json(),
        )

        success = await svc.poll_and_process(session)
        assert success


@pytest.mark.asyncio
async def test_message_job_just_completes(queue_service, svc, db_service):
    with db_service.get_session() as session:
        job = CommandJob(
            id="test-message",
            channel="test.message.response",
            method="MESSAGE",
            data={"test": 1},
            finished_at=0,
            send_at=0,
            state=JobState.IDLE,
            started_at=int(datetime.now().timestamp()),
            url="",
        )

        queue_service.get_next.return_value = job
        success = await svc.poll_and_process(session)
        assert success
