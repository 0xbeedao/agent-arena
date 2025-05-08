from statemachine import State
from statemachine import StateMachine


class RequestMachine(StateMachine):
    """
    State machine for handling async request flow.

    States:
    - idle: Waiting for a job
    - request: Job received, preparing to request
    - requesting: Sending HTTP request
    - response: HTTP response received, processing
    - waiting: Waiting for external completion
    - fail: Request failed
    - complete: Request completed successfully
    """

    idle = State("IDLE", initial=True)
    request = State("REQUEST")
    requesting = State("REQUESTING")
    response = State("RESPONSE")
    waiting = State("WAITING", final=True)
    fail = State("FAIL", final=True)
    complete = State("COMPLETE", final=True)

    # Transitions
    get_job = idle.to(request)
    start_request = request.to(requesting)
    http_error = requesting.to(fail)
    http_ok = requesting.to(response)
    malformed_response = response.to(fail)
    state_failure = response.to(fail)
    state_complete = response.to(complete)
    state_pending = response.to(waiting)
    wakeup = waiting.to(request)

    def __init__(self, job=None, logging=None):
        """
        Initialize the request machine.

        :param job: Optional job or context object for the request.
        """
        self.job = job
        self.log = logging.get_logger(
            "requestmachine", job=getattr(job, "id", None) if job else "none"
        )
        super().__init__()

    def on_enter_idle(self):
        """Called when entering the IDLE state."""

    def on_enter_request(self):
        """Called when entering the REQUEST state."""

    def on_enter_requesting(self):
        """Called when entering the REQUESTING state."""

    def on_enter_response(self):
        """Called when entering the RESPONSE state."""

    def on_enter_waiting(self):
        """Called when entering the WAITING state."""

    def on_enter_fail(self):
        """Called when entering the FAIL state."""

    def on_enter_complete(self):
        """Called when entering the COMPLETE state."""

    def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target, event):
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")
