from datetime import datetime
from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from pydantic import Field

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.models.agent import AgentDTO
from agentarena.models.job import CommandJob
from agentarena.models.job import JobResponseState
from agentarena.models.job import JobState
from agentarena.models.job import UrlJobRequest
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus


class DebugBatchRequest(UrlJobRequest):
    urls: List[str]


class DebugController:
    """
    Provides debug/raw endpoints for testing and discovery in Scheduler Server
    """

    def __init__(
        self,
        base_path: str = "/api",
        agent_service: ModelService[AgentDTO] = Field(
            description="The Agent DTO Service"
        ),
        job_service: ModelService[CommandJob] = Field(description="Job Model service"),
        message_broker: MessageBroker = Field(),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.agent_service = agent_service
        self.base_path = f"{base_path}/debug"
        self.job_service = job_service
        self.log = logging.get_logger("controller", path=self.base_path)
        self._subscribed = []
        self.message_broker = message_broker

    async def get_job(self, job_id: str = Field(description="job ID to fetch")):
        job, response = await self.job_service.get(job_id)
        if not response.success:
            raise HTTPException(status_code=404, detail=job_id)
        return job

    async def send_request_job(self, req: UrlJobRequest) -> CommandJob:
        delay = req.delay or 0
        send_at = int(datetime.now().timestamp()) + delay
        job = CommandJob(
            channel="scheduler.debug.request",
            data=req.data,
            method=req.method or "GET",
            priority=5,
            send_at=send_at,
            state=JobState.IDLE.value,
            started_at=0,
            finished_at=0,
            url=req.url,
        )
        sent, response = await self.job_service.create(job)
        if not response.success or not sent:
            raise HTTPException(status_code=500, detail=response)
        self.log.info("Created job", job=sent.id)
        return sent

    async def send_batch_job(self, req: DebugBatchRequest) -> CommandJob:
        delay = req.delay or 0
        send_at = int(datetime.now().timestamp()) + delay

        batchreq = CommandJobRequest(
            id="",
            channel="scheduler.debug.batch",
            data=req.data or {},
            method="MESSAGE",
            priority=5,
            send_at=send_at,
            state=JobState.IDLE.value,
            url="",
        )
        batch, response = await self.job_service.create(batchreq.to_job())
        if not response.success or batch is None:
            raise HTTPException(status_code=500, detail=response)
        log = self.log.bind(batch=batch.id)
        log.info("Created batch")
        batchreq.id = batch.id
        requests = [
            UrlJobRequest(
                url=url,
                method="GET",
                data={},
                delay=0,
            )
            for url in req.urls
        ]

        children = [batchreq.make_child(req) for req in requests]

        for child in children:
            child, _ = await self.job_service.create(child.to_job())
            if child is not None:
                log.info("Created child", child=child.id)

        return batch

    async def healthOK(self):
        self.log.info("health OK")
        return HealthResponse(
            job_id="1",
            state=JobResponseState.COMPLETED.value,
            message="test",
            data=HealthStatus(name="debug_controller", state="OK", version="1"),
        )

    async def log_message(self, *args, **kwargs):
        self.log.info("received message", args=args, **kwargs)

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["debug"])

        @router.post("/batch", response_model=CommandJob)
        async def send_batch(req: DebugBatchRequest = Body(...)):
            return await self.send_batch_job(req)

        @router.get("/job/{job_id}", response_model=CommandJob)
        async def get_job(job_id: str):
            return await self.get_job(job_id)

        @router.post("/request", response_model=CommandJob)
        async def send_request(req: UrlJobRequest = Body(...)):
            return await self.send_request_job(req)

        @router.get("/health", response_model=HealthResponse)
        async def health():
            return await self.healthOK()

        return router

    async def subscribe_yourself(self, message_broker: MessageBroker):
        if not self._subscribed:
            self.log.info("Subscribing to scheduler.debug.>")
            sub = await message_broker.client.subscribe(
                "scheduler.debug.>", cb=self.log_message
            )
            self._subscribed.append(sub)

    async def unsubscribe_yourself(self):
        if self._subscribed:
            for sub in self._subscribed:
                await sub.unsubscribe()
