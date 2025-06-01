import nats
from nats.aio.client import Client as NatsClient
from nats.aio.msg import Msg
from sqlmodel import Field

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobBatchRequest
from agentarena.models.job import JobResponse
from agentarena.models.job import ModelChangeMessage


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
        self.prefix = ""
        self.uuid_service = uuid_service
        self.log = logging.get_logger("factory")

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
        json = payload.model_dump_json().encode("utf-8")
        if self.prefix and not channel.startswith(f"{self.prefix}."):
            channel = f"{self.prefix}.{channel}"
        await self.client.publish(channel, json)

    async def publish_response(self, msg: Msg, response: JobResponse):
        """
        Publish a response to the message broker.
        """
        channel = msg.reply or response.channel
        log = self.log.bind(job_id=response.job_id, channel=channel)
        if not channel:
            log.warn("No channel specified for response", job_id=response.job_id)
            return
        log.debug("Publishing response", job_id=response.job_id)
        json = response.model_dump_json()

        if (
            self.prefix
            and channel == response.channel
            and not channel.startswith(f"{self.prefix}.")
        ):
            channel = f"{self.prefix}.{channel}"
        log.debug("Publishing response to channel", channel=channel, response=json)
        await self.client.publish(channel, json.encode("utf-8"))

    async def send_job(self, req: CommandJob):
        """
        sends a job to the scheduler
        """
        obj_id = self.uuid_service.ensure_id(req)
        obj = req.model_copy()
        obj.id = obj_id
        if (
            obj.channel
            and self.prefix
            and not obj.channel.startswith(f"{self.prefix}.")
        ):
            obj.channel = f"{self.prefix}.{obj.channel}"
        json = obj.model_dump_json()

        await self.send_message("arena.request.job", json)

    async def send_batch(self, req: CommandJobBatchRequest):
        """
        Sends a batch to the scheduler
        """
        batch_id = self.uuid_service.ensure_id(req.batch)
        batch: CommandJob = req.batch.model_copy()
        batch.id = batch_id
        # batch should not get picked up until complete
        batch.state = JobState.REQUEST
        await self.send_job(batch)
        jobs = [batch.make_child(req) for req in req.children]

        for job in jobs:
            await self.send_job(job)

    async def send_message(self, channel: str, payload: str):
        self.log.debug("Sending message", channel=channel, payload=payload)
        await self.client.publish(channel, payload.encode("utf-8"))

    async def send_response(self, channel: str, res: JobResponse):
        """
        Send a response from the scheduler
        """
        self.log.debug(f"publishing response: {res.job_id}")
        json = res.model_dump_json()
        dest = channel
        if self.prefix and not channel.startswith(f"{self.prefix}."):
            dest = f"{self.prefix}.{dest}"

        await self.send_message(dest, json)
