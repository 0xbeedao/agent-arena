import pytest

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.constants import JobState
from agentarena.models.job import CommandJob
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.statemachines.request_machine import RequestMachine
from agentarena.statemachines.request_machine import RequestState


@pytest.fixture
def logging():
    return LoggingService(True)


def make_job():
    return CommandJob(
        id="testjob",
        channel="test.arena.job",
        url="http://localhost:8000/test",
        method="GET",
        state=JobState.IDLE,
        data='{"test": "toast"}',
    )


def make_success_response() -> JobResponse:
    return JobResponse(
        job_id="test-response",
        state=JobResponseState.COMPLETE,
        data='{"check": "yep"}',
    )


def make_pending_response() -> JobResponse:
    return JobResponse(job_id="test-response", state=JobResponseState.PENDING)


@pytest.mark.asyncio
async def test_initial_state(logging):
    job = make_job()
    machine = RequestMachine(job, logging=logging)
    await machine.activate_initial_state()  # type: ignore
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

    machine = RequestMachine(
        job,
        logging=logging,
        arena_url="http://localhost:8000",
        actor_url="http://localhost:8001",
    )

    await machine.activate_initial_state()  # type: ignore
    await machine.start_request("start")
    assert machine.current_state.id == RequestState.COMPLETE.value


@pytest.mark.asyncio
async def test_fail_call(logging, httpx_mock):
    job = make_job()
    httpx_mock.add_response(
        status_code=404,
        method="GET",
        url="http://localhost:8000/test",
    )

    machine = RequestMachine(
        job,
        logging=logging,
        arena_url="http://localhost:8000",
        actor_url="http://localhost:8001",
    )

    await machine.activate_initial_state()  # type: ignore
    await machine.start_request("test")
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

    machine = RequestMachine(
        job,
        logging=logging,
        arena_url="http://localhost:8000",
        actor_url="http://localhost:8001",
    )

    await machine.activate_initial_state()  # type: ignore
    await machine.start_request("test")
    assert machine.current_state.id == RequestState.WAITING.value
