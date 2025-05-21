from typing import Any
from typing import Mapping

import nats
import orjson
from nats.aio.client import Client as NatsClient
from pydantic import Field

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobBatchRequest
from agentarena.models.job import JobResponse
from agentarena.models.job import JobState


async def get_message_broker_connection(
    nats_url: str,
    logging: LoggingService,
):
    """DI method to instantiate a NATS connection"""
    assert nats_url
    logging.get_logger("factory").info("Setup NATS message broker", url=nats_url)
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

        self.log.debug("Publishing", job=json)
        await self.client.publish(obj.channel, json.encode("utf-8"))

    async def send_batch(self, req: CommandJobBatchRequest):
        """
        Sends a batch to the scheduler
        """
        batch_id = self.uuid_service.ensure_id(req.batch)
        batch: CommandJob = req.batch.model_copy()
        batch.id = batch_id
        # batch should not get picked up until complete
        batch.state = JobState.REQUEST.value
        await self.send_job(batch)
        jobs = [batch.make_child(req) for req in req.children]

        for job in jobs:
            await self.send_job(job)

    async def send_message(self, channel: str, payload: Mapping[str, Any]):
        self.log.debug("Sending message", channel=channel, payload=payload)
        json = orjson.dumps(payload)
        await self.client.publish(channel, json)

    async def send_response(self, channel: str, res: JobResponse):
        """
        Send a response from the scheduler
        """
        self.log.debug(f"publishing response: {res.job_id}")
        json = res.model_dump_json()
        dest = channel
        if self.prefix and not channel.startswith(f"{self.prefix}."):
            dest = f"{self.prefix}.{dest}"

        await self.client.publish(dest, json.encode("utf-8"))
