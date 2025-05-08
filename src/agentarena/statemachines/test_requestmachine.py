from agentarena.factories.logger_factory import LoggingService
from agentarena.statemachines.request_machine import RequestMachine


class MockJob:
    def __init__(self, job_id="job1"):
        self.id = job_id


def logging():
    return LoggingService(True)


def make_job(job_id="job1"):
    return MockJob(job_id)


def test_initial_state():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    assert machine.current_state.id == "idle"


def test_get_job_transition():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    machine.get_job()
    assert machine.current_state.id == "request"


def test_start_request_transition():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    machine.get_job()
    machine.start_request()
    assert machine.current_state.id == "requesting"


def test_http_error_transition():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    machine.get_job()
    machine.start_request()
    machine.http_error()
    assert machine.current_state.id == "fail"
    assert machine.current_state.final


def test_http_ok_transition():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    machine.get_job()
    machine.start_request()
    machine.http_ok()
    assert machine.current_state.id == "response"


def test_malformed_response_transition():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    machine.get_job()
    machine.start_request()
    machine.http_ok()
    machine.malformed_response()
    assert machine.current_state.id == "fail"
    assert machine.current_state.final


def test_state_failure_transition():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    machine.get_job()
    machine.start_request()
    machine.http_ok()
    machine.state_failure()
    assert machine.current_state.id == "fail"
    assert machine.current_state.final


def test_state_complete_transition():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    machine.get_job()
    machine.start_request()
    machine.http_ok()
    machine.state_complete()
    assert machine.current_state.id == "complete"
    assert machine.current_state.final


def test_full_success_sequence():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    assert machine.current_state.id == "idle"
    machine.get_job()
    assert machine.current_state.id == "request"
    machine.start_request()
    assert machine.current_state.id == "requesting"
    machine.http_ok()
    assert machine.current_state.id == "response"
    machine.state_complete()
    assert machine.current_state.id == "complete"
    assert machine.current_state.final


def test_full_failure_sequence():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    assert machine.current_state.id == "idle"
    machine.get_job()
    assert machine.current_state.id == "request"
    machine.start_request()
    assert machine.current_state.id == "requesting"
    machine.http_error()
    assert machine.current_state.id == "fail"
    assert machine.current_state.final


def test_on_enter_methods_are_callable():
    job = make_job()
    machine = RequestMachine(job=job, logging=logging())
    # These are empty, but we check they exist and are callable
    for method in [
        machine.on_enter_idle,
        machine.on_enter_request,
        machine.on_enter_requesting,
        machine.on_enter_response,
        machine.on_enter_waiting,
        machine.on_enter_fail,
        machine.on_enter_complete,
    ]:
        method()  # Should not raise
