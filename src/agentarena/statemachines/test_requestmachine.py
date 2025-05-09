import httpx
import pytest
from pydantic import BaseModel

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.statemachines.request_machine import RequestMachine
from agentarena.statemachines.request_machine import RequestState


class MockJob(BaseModel):
    id: str
    url: str
    method: str
    payload: str


@pytest.fixture
def logging():
    return LoggingService(True)


def make_job():
    return MockJob(
        id="testjob",
        url="http://localhost:8000/test",
        method="GET",
        payload='{"test": "toast"}',
    )


def make_success_response() -> JobResponse:
    return JobResponse(
        job_id="test-response",
        state=JobResponseState.COMPLETED.value,
        data={"check": "yep"},
    )


def make_pending_response() -> JobResponse:
    return JobResponse(job_id="test-response", state=JobResponseState.PENDING.value)


@pytest.mark.asyncio
async def test_initial_state(logging):
    job = make_job()
    machine = RequestMachine(job, logging=logging)
    await machine.activate_initial_state()
    assert machine.current_state.id == RequestState.IDLE.value


@pytest.mark.asyncio
async def test_success_call(logging, httpx_mock):
    job = make_job()
    httpx_mock.add_response(
        status_code=200,
        method="GET",
        url="http://localhost:8000/test",
        content=make_success_response().model_dump_json(),
    )

    with httpx.Client() as client:
        machine = RequestMachine(job, logging=logging, http_client=client)

        await machine.activate_initial_state()
        await machine.start_request()
        assert machine.current_state.id == RequestState.COMPLETE.value


@pytest.mark.asyncio
async def test_fail_call(logging, httpx_mock):
    job = make_job()
    httpx_mock.add_response(
        status_code=404,
        method="GET",
        url="http://localhost:8000/test",
    )

    with httpx.Client() as client:
        machine = RequestMachine(job, logging=logging, http_client=client)

        await machine.activate_initial_state()
        await machine.start_request()
        assert machine.current_state.id == RequestState.FAIL.value


@pytest.mark.asyncio
async def test_pending_call(logging, httpx_mock):
    job = make_job()
    httpx_mock.add_response(
        status_code=200,
        method="GET",
        url="http://localhost:8000/test",
        content=make_pending_response().model_dump_json(),
    )

    with httpx.Client() as client:
        machine = RequestMachine(job, logging=logging, http_client=client)

        await machine.activate_initial_state()
        await machine.start_request()
        assert machine.current_state.id == RequestState.WAITING.value
