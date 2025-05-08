from datetime import datetime
from unittest.mock import AsyncMock, Mock

from httpx import Response
import pytest

from agentarena.factories.db_factory import get_database
from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import BaseAsyncJobResponse, JobState, JsonRequestJob
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService
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
        started_at=datetime.now().timestamp(),
        url="/test",
    )


@pytest.fixture
def logging():
    return LoggingService(True)


@pytest.fixture
def queue_service():
    service = AsyncMock()
    return service


@pytest.fixture
def result_handler():
    service = AsyncMock()
    return service


@pytest.fixture
def http_factory():
    service = Mock()
    return service


@pytest.mark.asyncio
async def test_no_jobs(queue_service, result_handler, logging):
    svc = RequestService(
        queue_service=queue_service,
        result_handler=result_handler,
        http_client_factory=Mock(),
        logging=logging,
    )
    queue_service.get_next.return_value = None
    response = await svc.poll_and_process()
    assert response == False
    queue_service.get_next.assert_awaited_once()


@pytest.mark.asyncio
async def test_poll_job_success(queue_service, http_factory, result_handler, logging):
    client = Mock()
    client.GET.return_value
    http_factory.return_value = client
    svc = RequestService(
        queue_service=queue_service,
        result_handler=result_handler,
        http_client_factory=http_factory,
        logging=logging,
    )
    job = make_job()
    queue_service.get_next.return_value = job

    job_response = BaseAsyncJobResponse(job_id="test", state="completed")

    client.request.return_value = Response(
        status_code="200", content=job_response.model_dump_json()
    )

    success = svc.poll_and_process()
    assert success

    # need to finish wiring the service, and test that it got marked complete

    # theoretical impl
