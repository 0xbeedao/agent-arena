from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import pytest

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.event import JobEvent
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.models.job import JobState
from agentarena.models.job import JsonRequestJob
from agentarena.services.request_service import RequestService


def make_job(name: str):
    return JsonRequestJob(
        id=name,
        attempt=1,
        caller="test",
        command="test",
        method="GET",
        payload="{'test': 1}",
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
def event_bus():
    mock_bus = AsyncMock()
    return mock_bus


def make_success_response() -> JobResponse:
    return JobResponse(
        job_id="test-response",
        state=JobResponseState.COMPLETED.value,
        data={"check": "yep"},
    )


def make_pending_response() -> JobResponse:
    return JobResponse(
        job_id="test-response",
        state=JobResponseState.PENDING.value,
        eta=int(datetime.now().timestamp() + 100),
    )


@pytest.mark.asyncio
async def test_no_jobs(queue_service, event_bus, logging):
    svc = RequestService(
        event_bus=event_bus,
        queue_service=queue_service,
        http_client_factory=httpx.Client,
        logging=logging,
    )
    queue_service.get_next.return_value = None
    response = await svc.poll_and_process()
    assert response is False
    queue_service.get_next.assert_awaited_once()
    # No event is published when there are no jobs
    event_bus.publish.assert_not_awaited()


@pytest.mark.asyncio
async def test_poll_job_success(queue_service, event_bus, logging, httpx_mock):
    svc = RequestService(
        event_bus=event_bus,
        queue_service=queue_service,
        http_client_factory=httpx.Client,
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
    event_bus.publish.assert_awaited_once()
    # Check the event content/state
    published_event = event_bus.publish.await_args.args[0]
    assert isinstance(published_event, JobEvent)
    assert published_event.state == JobResponseState.COMPLETED.value


@pytest.mark.asyncio
async def test_poll_job_pending(queue_service, event_bus, logging, httpx_mock):
    svc = RequestService(
        event_bus=event_bus,
        queue_service=queue_service,
        http_client_factory=httpx.Client,
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
    # No event is published for pending jobs (WAITING state)
    event_bus.publish.assert_not_awaited()
