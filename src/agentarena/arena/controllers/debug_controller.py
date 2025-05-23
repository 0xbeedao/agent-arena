from typing import List

from fastapi import APIRouter
from nats.aio.client import Client as NatsClient
from sqlmodel import Field

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.models.job import JobResponseState
from agentarena.models.job import UrlJobRequest
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus


class DebugBatchRequest(UrlJobRequest):
    urls: List[str]


class DebugController:
    """
    Provides debug/raw endpoints for testing and discovery.
    """

    def __init__(
        self,
        base_path: str = "/api",
        message_broker: NatsClient = Field(description="Message broker client"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.base_path = f"{base_path}/debug"
        self.message_broker = message_broker
        self.log = logging.get_logger("controller", path=self.base_path)

    # async def send_request_job(self, req: UrlJobRequest) -> None:
    #     delay = req.delay if req.delay else 0
    #     send_at = int(datetime.now().timestamp() + delay)
    #     job = CommandJobRequest(
    #         id="",
    #         channel="job.request.url",
    #         data=req.data,
    #         method=req.method if req.method else "GET",
    #         priority=5,
    #         send_at=send_at,
    #         state=JobState.IDLE.value,
    #         url=req.url,
    #     )
    #     try:
    #         await self.message_broker.publish(job)
    #     except Exception as e:
    #         self.log.error("error connecting to NATS", error=e)

    # async def send_batch_job(self, req: DebugBatchRequest) -> CommandJob:
    #     delay = req.delay if req.delay else 0
    #     send_at = int(datetime.now().timestamp() + delay)
    #     batch = CommandJob(
    #         channel="job.request.url",
    #         data="$JOB$",
    #         method="MESSAGE",
    #         priority=5,
    #         send_at=send_at,
    #         state=JobState.IDLE.value,
    #         started_at=0,
    #         finished_at=0,
    #         url="arena.debug.batch.final",
    #     )
    #     requests = [
    #         UrlJobRequest(
    #             url=url,
    #             method="GET",
    #             data="",
    #             delay=0,
    #         )
    #         for url in req.urls
    #     ]

    #     sent = await self.q.send_batch(batch, requests)
    #     if not sent:
    #         raise HTTPException(status_code=500, detail="Invalid queue response")
    #     return sent

    async def healthOK(self):
        self.log.info("health OK")
        return HealthResponse(
            job_id="1",
            state=JobResponseState.COMPLETED.value,
            message="test",
            data=HealthStatus(name="debug_controller", state="OK", version="1"),
            url="",
        )

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["debug"])

        # @router.post("/batch", response_model=CommandJob)
        # async def send_request(req: DebugBatchRequest = Body(...)):
        #     return await self.send_batch_job(req)

        # @router.post("/event/{job_id}", response_model=JobResponse)
        # async def receive_event(job_id: str, req: str = Body(...)):
        #     return await self.event(job_id, req)

        # @router.get("/job/{job_id}", response_model=CommandJob)
        # async def get_job(job_id: str):
        #     return await self.get_job(job_id)

        # @router.post("/request", response_model=CommandJob)
        # async def send_request(req: UrlJobRequest = Body(...)):
        #     return await self.send_request_job(req)

        @router.get("/health", response_model=HealthResponse)
        async def health():
            return await self.healthOK()

        return router
