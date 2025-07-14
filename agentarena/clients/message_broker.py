from codecs import encode
from typing import Coroutine

import nats
from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg
from sqlmodel import Field

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.public import JobResponse
from agentarena.models.public import ModelChangeMessage


async def get_message_broker_connection(
    nats_url: str,
    logging: LoggingService,
):
    """DI method to instantiate a NATS connection"""
    assert nats_url
    log = logging.get_logger("factory")
    log.info("Setup NATS message broker", url=nats_url)
    nat_conn = await nats.connect(nats_url)
    yield nat_conn
    await nat_conn.drain()


class MessageBroker:
    def __init__(
        self,
        client: NatsClient = Field(),
        uuid_service: UUIDService = Field(),
        logging: LoggingService = Field(),
    ):
        self.client = client
        assert self.client is not None, "Message broker client is not set"
        self.uuid_service = uuid_service
        self.log = logging.get_logger("factory")

    async def nats(self) -> NatsClient:
        if isinstance(self.client, Coroutine):
            self.client = await self.client
        return self.client

    async def publish_model_change(self, channel: str, obj_id: str, detail=""):
        """
        Publish a model change to the message broker.
        """
        log = self.log.bind(channel=channel, obj_id=obj_id)
        log.debug("Publishing model change", detail=detail)
        payload = ModelChangeMessage(
            model_id=obj_id,
            detail=detail,
            action=channel.split(".")[-1],
        )
        json = encode(payload.model_dump_json(), "utf-8", "unicode_escape")

        client = await self.nats()
        await client.publish(channel, json)  # type: ignore

    async def publish_response(self, channel: str, response: JobResponse):
        """
        Publish a response to the message broker.
        """
        log = self.log.bind(job_id=response.job_id, channel=channel)
        if not channel:
            log.warn("No channel specified for response", job_id=response.job_id)
            return
        json = encode(response.model_dump_json(), "utf-8", "unicode_escape")

        log.debug("Publishing response to channel", channel=channel, response=json)
        client = await self.nats()
        await client.publish(channel, json)  # type: ignore

    async def request_job(
        self, channel: str, payload: str | bytes, timeout: float = 60.0
    ) -> Msg:
        """
        Request a job from the message broker.
        """
        if isinstance(payload, str):
            payload = encode(payload, "utf-8", "unicode_escape")
        elif isinstance(payload, bytes):
            pass
        else:
            self.log.error("Invalid payload type", channel=channel, payload=payload)
            raise ValueError(f"Invalid payload type: {type(payload)}")
        self.log.info("Requesting job", channel=channel, payload=f"{payload[:50]}...")
        client = await self.nats()
        response = await client.request(channel, payload, timeout=timeout)  # type: ignore
        self.log.debug("Received response", channel=channel, response=response)
        return response

    async def send_message(self, channel: str, payload: str | bytes):
        self.log.debug("Sending message", channel=channel, payload=payload)
        if isinstance(payload, str):
            to_send = encode(payload, "utf-8", "unicode_escape")
        elif isinstance(payload, bytes):
            to_send = payload
        else:
            raise ValueError(f"Invalid payload type: {type(payload)}")
        client = await self.nats()
        await client.publish(channel, to_send)  # type: ignore

    async def send_response(self, channel: str, res: JobResponse):
        """
        Send a response from the scheduler
        """
        self.log.debug(f"publishing response: {res.job_id}")
        json = res.model_dump_json()
        await self.send_message(channel, json)
