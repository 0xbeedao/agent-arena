from datetime import datetime

import nats
from fastapi import Depends
from nats.aio.client import Client as NatsClient
from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJobBatchRequest, JobResponse
from agentarena.models.job import CommandJobRequest
from agentarena.models.job import JobState
from agentarena.models.job import UrlJobRequest
from agentarena.services.uuid_service import UUIDService


async def get_message_broker_connection(
    nats_url: str,
    logging: LoggingService = Depends(),
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

    async def send_job(self, req: CommandJobRequest):
        """
        sends a job to the message broker
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
        batch_id = self.uuid_service.ensure_id(req.batch)
        batch: CommandJobRequest = req.batch.model_copy()
        batch.id = batch_id
        # batch should not get picked up until complete
        batch.state = JobState.REQUEST.value
        await self.send_job(batch)
        jobs = [batch.make_child(req) for req in req.children]

        for job in jobs:
            await self.send_job(job)

    async def send_response(self, channel: str, res: JobResponse):
        self.log.debug(f"publishing response: {res.job_id}")
        json = res.model_dump_json()
        dest = channel
        if self.prefix and not channel.startswith(f"{self.prefix}."):
            dest = f"{self.prefix}.{dest}"

        await self.client.publish(dest, json.encode("utf-8"))
