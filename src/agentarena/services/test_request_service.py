from datetime import datetime
from unittest.mock import AsyncMock

import httpx
import pytest

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import BaseAsyncJobResponse
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


class ResultHandler:
    def __init__(self):
        self.hits = []
        self.rejects = []

    async def send_payload(self, job, payload):
        self.hits.append((job, payload))
        return None

    async def send_rejection(self, job, reject):
        self.rejects.append((job, reject))

    def count(self):
        return len(self.hits) + len(self.rejects)


@pytest.fixture
def result_handler():
    service = ResultHandler()
    return service


def make_success_response() -> BaseAsyncJobResponse:
    return BaseAsyncJobResponse(
        job_id="test-response",
        state=JobResponseState.COMPLETED.value,
        data={"check": "yep"},
    )


def make_pending_response() -> BaseAsyncJobResponse:
    return BaseAsyncJobResponse(
        job_id="test-response",
        state=JobResponseState.PENDING.value,
        eta=int(datetime.now().timestamp() + 100),
    )


@pytest.mark.asyncio
async def test_no_jobs(queue_service, result_handler, logging):
    svc = RequestService(
        queue_service=queue_service,
        result_handler=result_handler,
        http_client_factory=httpx.Client,
        logging=logging,
    )
    queue_service.get_next.return_value = None
    response = await svc.poll_and_process()
    assert response == False
    queue_service.get_next.assert_awaited_once()
    assert result_handler.count() == 0


@pytest.mark.asyncio
async def test_poll_job_success(queue_service, result_handler, logging, httpx_mock):
    svc = RequestService(
        queue_service=queue_service,
        result_handler=result_handler,
        http_client_factory=httpx.Client,
        logging=logging,
    )
    job = make_job("xxx")
    # make queue return the job
    queue_service.get_next.return_value = job
    queue_service.update_state.return_value = make_job("xxx")

    # when the job executes, it will call the client
    # so return the successful job response
    job_response = make_success_response()
    httpx_mock.add_response(
        status_code=200,
        method="GET",
        url="http://localhost:8000/xxx",
        content=job_response.model_dump_json(),
    )

    success = await svc.poll_and_process()
    assert success
    assert len(result_handler.hits) == 1
    assert result_handler.count() == 1


@pytest.mark.asyncio
async def test_poll_job_pending(queue_service, result_handler, logging, httpx_mock):
    svc = RequestService(
        queue_service=queue_service,
        result_handler=result_handler,
        http_client_factory=httpx.Client,
        logging=logging,
    )
    job = make_job("xxx")
    # make queue return the job
    queue_service.get_next.return_value = job
    queue_service.requeue_job.return_value = make_job("yyy")

    # when the job executes, it will call the client
    # so return the successful job response
    job_response = make_pending_response()
    httpx_mock.add_response(
        status_code=200,
        method="GET",
        url="http://localhost:8000/xxx",
        content=job_response.model_dump_json(),
    )

    success = await svc.poll_and_process()
    assert success
    assert result_handler.count() == 0
