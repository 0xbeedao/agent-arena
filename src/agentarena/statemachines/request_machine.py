import json
from enum import Enum

import httpx
from sqlmodel import Field
from statemachine import State
from statemachine import StateMachine

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob
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
    waiting = State(RequestState.WAITING.value, final=True)
    fail = State(RequestState.FAIL.value, final=True)
    complete = State(RequestState.COMPLETE.value, final=True)

    # Transitions
    start_request = idle.to(request)
    receive_response = request.to(response, cond="is_valid_response") | request.to(
        fail, unless="is_valid_response"
    )
    sent_message = request.to(complete)
    http_error = request.to(fail)
    http_ok = request.to(response)
    malformed_response = response.to(fail)
    state_failure = response.to(fail)
    state_complete = response.to(complete)
    state_pending = response.to(waiting)

    def __init__(
        self,
        job: CommandJob,
        arena_url: str = Field(description="url of arena server"),
        message_broker: MessageBroker = Field(),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """
        Initialize the request machine.

        :param job: Optional job or context object for the request.
        """
        self.arena_url = arena_url
        self.job = job
        self.response_object: JobResponse | None = None
        self.log = logging.get_logger("machine", job=job.id)
        self.message_broker = message_broker
        super().__init__()

    async def on_enter_request(self):
        """Called when entering the REQUEST state."""
        method = self.job.method.lower()
        if method == "message":
            return await self.send_message()
        return await self.send_request()

    async def send_message(self):
        job = self.job
        log = self.log.bind(job=job, method="send_message")
        try:
            # url on the outbound, channel on final response
            channel = job.url or None
            if not channel:
                log.warn("No channel available for message, cannot send")
                return None
            data = job.data or {}
            log = log.bind(channel=channel, data=data)
            log.info("sending message")
            await self.message_broker.send_message(channel, data)
            await self.sent_message("")
        except Exception as e:
            self.log.error(
                "Error while sending message",
                error=e,
            )

    async def send_request(self):
        """
        Send the request via HTTPX
        """
        method = self.job.method.lower()
        try:
            url = self._resolve_url()
            data = self.job.data
            self.log.info("requesting", url=url, data=data)
            response = httpx.Client().request(method, url, data=data)
            await self.receive_response(response)
        except Exception as e:
            self.log.error(
                f"Error while fetching",
                url=self.job.url,
                error=e,
            )
            await self.http_error(e)

    def is_valid_response(self, response):
        if response.status_code >= 400:
            return False
        json = response.json()
        try:
            obj = JobResponse.model_validate(json)
            self.log.info(f"parsed correctly? {obj is not None}")
            return True
        except Exception as e:
            self.log.error(f"message could not be parsed: {json}", error=e)
        return False

    async def on_enter_response(self, response):
        """Called when entering the RESPONSE state."""
        json = response.json()
        self.response_object = JobResponse.model_validate(json)
        state = self.response_object.state
        self.log.info("responder state is", responder=state)
        if state == JobResponseState.FAIL.value:
            await self.state_failure("")
        elif state == JobResponseState.PENDING.value:
            await self.state_pending("")
        elif state == JobResponseState.COMPLETED.value:
            await self.state_complete("")
        else:
            self.log.warn(f"invalid state: {state}")
            await self.malformed_response("")

    def on_enter_state(self, target, event):
        self.log = self.log.bind(state=target.id)
        if target.final:
            self.log.debug(f"{self.name} enter final state: {target.id} from {event}")
        # else:
        #     self.log.debug(f"{self.name} enter: {target.id} from {event}")

    def clean_data(self, data: str | None) -> object | None:
        if not data:
            return None
        data = data.strip()
        if not data:
            return None
        try:
            obj = json.loads(data)
        except json.JSONDecodeError as e:
            # try again, with quotes
            orig = data
            data = f'"{data}"'
            try:
                obj = json.loads(data)
            except json.JSONDecodeError as e:
                self.log.warn(f"Could not parse data {orig}", error=e)
                obj = None

        if obj:
            return obj
        return None

    def _resolve_url(self) -> str:
        """Expand url, if needed"""
        url = self.job.url or ""
        url = url.replace("$JOB$", self.job.id)
        url = url.replace("$ARENA$", self.arena_url)
        self.log.info(f"resolved url is {url} from {self.job.url}")
        return url
