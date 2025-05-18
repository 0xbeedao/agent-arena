from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.models.job import JobState
from agentarena.scheduler.services.request_service import RequestService


def make_job(name: str):
    return CommandJob(
        id=name,
        channel="test.command",
        method="GET",
        data={"test": 1},
        finished_at=0,
        send_at=0,
        state=JobState.IDLE.value,
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


def make_success_response() -> JobResponse:
    return JobResponse(
        job_id="test-response",
        state=JobResponseState.COMPLETED.value,
        data={"check": "yep"},
    )


def make_pending_response() -> JobResponse:
    return JobResponse(
        job_id="test-response", state=JobResponseState.PENDING.value, delay=1
    )


@pytest.mark.asyncio
async def test_no_jobs(queue_service, logging):
    svc = RequestService(
        queue_service=queue_service,
        logging=logging,
    )
    queue_service.get_next.return_value = None
    response = await svc.poll_and_process()
    assert response is False
    queue_service.get_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_job_success(queue_service, logging, httpx_mock):
    svc = RequestService(
        arena_url="http://localhost:8000",
        queue_service=queue_service,
        logging=logging,
    )
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

    success = await svc.poll_and_process()
    assert success


@pytest.mark.asyncio
async def test_poll_job_pending(queue_service, logging, httpx_mock):
    svc = RequestService(
        arena_url="http://localhost:8000",
        queue_service=queue_service,
        logging=logging,
    )
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

    success = await svc.poll_and_process()
    assert success


@pytest.mark.asyncio
async def test_message_job_just_completes(queue_service, logging, message_broker):
    svc = RequestService(
        arena_url="http://localhost:8000",
        queue_service=queue_service,
        logging=logging,
    )
    job = CommandJob(
        id="test-message",
        channel="test.message.response",
        method="MESSAGE",
        data={"test": 1},
        finished_at=0,
        send_at=0,
        state=JobState.IDLE.value,
        started_at=int(datetime.now().timestamp()),
        url="",
    )

    queue_service.get_next.return_value = job
    success = await svc.poll_and_process()
    assert success
