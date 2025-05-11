from enum import Enum

from httpx import Client
from pydantic import Field
from statemachine import State
from statemachine import StateMachine

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob
from agentarena.models.job import JobCommandType
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState


class RequestState(Enum):
    IDLE = "idle"
    REQUEST = "request"
    RESPONSE = "response"
    WAITING = "waiting"
    FAIL = "fail"
    COMPLETE = "complete"


class RequestMachine(StateMachine):
    """
    State machine for handling async request flow.

    States:
    - idle: Waiting for a job
    - request: Job received, requesting
    - response: HTTP response received, processing
    - waiting: Waiting for external completion
    - fail: Request failed
    - complete: Request completed successfully
    """

    idle = State(RequestState.IDLE.value, initial=True)
    request = State(RequestState.REQUEST.value)
    response = State(RequestState.RESPONSE.value)
    waiting = State(RequestState.WAITING, final=True)
    fail = State(RequestState.FAIL, final=True)
    complete = State(RequestState.COMPLETE, final=True)

    # Transitions
    start_request = idle.to(request)
    receive_response = request.to(response, cond="is_valid_response") | request.to(
        fail, unless="is_valid_response"
    )
    http_error = request.to(fail)
    http_ok = request.to(response)
    malformed_response = response.to(fail)
    state_failure = response.to(fail)
    state_complete = response.to(complete)
    state_pending = response.to(waiting)

    def __init__(
        self,
        job: CommandJob,
        http_client: Client = None,
        logging: LoggingService = Field(desciption="Logger factory"),
    ):
        """
        Initialize the request machine.

        :param job: Optional job or context object for the request.
        """
        assert job.command == JobCommandType.REQUEST.value
        self.job = job
        self.http_client = http_client
        self.response_object: JobResponse = None
        self.log = logging.get_logger("requestmachine", job=job.id)
        super().__init__()

    async def on_enter_request(self):
        """Called when entering the REQUEST state."""
        method = self.job.method.lower()
        try:
            url = self._resolve_url()
            self.log.info("requesting", url=url)
            response = self.http_client.request(method, url, data=self.job.data)
            await self.receive_response(response)
        except Exception as e:
            self.log.error(
                f"Error while fetching",
                url=self.job.url,
                error=e,
            )
            await self.http_error()  # FAIL

    def is_valid_response(self, response):
        if response.status_code >= 400:
            return False
        try:
            json = response.json()
            obj = JobResponse.model_validate(json)
            self.log.info(f"parsed correctly? {obj is not None}")
            return True
        except Exception as e:
            self.log.error(f"message could not be parsed: {e}")
        return False

    def on_enter_response(self, response):
        """Called when entering the RESPONSE state."""
        json = response.json()
        self.response_object = JobResponse.model_validate(json)
        state = self.response_object.state
        self.log.info("responder state is", responder=state)
        if state == JobResponseState.FAIL.value:
            self.state_failure()
        elif state == JobResponseState.PENDING.value:
            self.state_pending()
        elif state == JobResponseState.COMPLETED.value:
            self.state_complete()
        else:
            self.log.warn(f"invalid state: {state}")
            self.malformed_response()

    def after_transition(self, event, source, target):
        self.log.debug(f"{self.name} after: {source.id}--({event})-->{target.id}")

    def on_enter_state(self, target, event):
        self.log = self.log.bind(state=target.id)
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        else:
            self.log.debug(f"{self.name} enter: {target.id} from {event}")

    def _resolve_url(self) -> str:
        """Expand url, if needed"""
        url = self.job.url
        url = url.replace("$JOB$", self.job.id)
        return url
