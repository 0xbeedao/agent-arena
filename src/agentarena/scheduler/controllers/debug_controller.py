from datetime import datetime
from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from pydantic import Field

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.agent import AgentDTO
from agentarena.models.job import CommandJob
from agentarena.models.job import JobCommandType
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.models.job import JobState
from agentarena.models.job import UrlJobRequest
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus
from agentarena.core.services.model_service import ModelService


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
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.agent_service = agent_service
        self.base_path = f"{base_path}/debug"
        self.job_service = job_service
        self.log = logging.get_logger("controller", path=self.base_path)

    async def event(self, job_id: str, event: str) -> JobResponse:
        """
        A callback event from the scheduler
        """
        self.log.bind(job_id=job_id)
        self.log.info(f"Received event {event}")
        return JobResponse(
            job_id=job_id,
            delay=0,
            message="OK",
            state=JobResponseState.COMPLETED.value,
        )

    async def get_job(self, job_id: str = Field(description="job ID to fetch")):
        job, response = await self.job_service.get(job_id)
        if not response.success:
            raise HTTPException(status_code="404", detail=job_id)
        return job

    async def send_request_job(self, req: UrlJobRequest) -> CommandJob:
        job = CommandJob(
            channel=JobCommandType.REQUEST.value,
            data=req.data,
            method=req.method,
            priority=5,
            send_at=int(datetime.now().timestamp() + req.delay),
            state=JobState.IDLE.value,
            started_at=0,
            finished_at=0,
            url=req.url,
        )
        sent = await self.q.send_job(job)
        if not sent:
            raise HTTPException(status_code="500", detail="Invalid queue response")
        return sent

    async def send_batch_job(self, req: DebugBatchRequest) -> CommandJob:
        batch = CommandJob(
            channel=JobCommandType.BATCH.value,
            data=req.data or "",
            method="POST",
            priority=5,
            send_at=int(datetime.now().timestamp() + req.delay),
            state=JobState.IDLE.value,
            started_at=0,
            finished_at=0,
            url=f"$ARENA${self.base_path}/event/$JOB$",
        )
        requests = [
            UrlJobRequest(
                url=url,
                method="GET",
                data="",
                delay=0,
            )
            for url in req.urls
        ]

        sent = await self.q.send_batch(batch, requests)
        if not sent:
            raise HTTPException(status_code="500", detail="Invalid queue response")
        return sent

    async def healthOK(self):
        self.log.info("health OK")
        return HealthResponse(
            job_id="1",
            state=JobResponseState.COMPLETED.value,
            message="test",
            data=HealthStatus(name="debug_controller", state="OK", version="1"),
        )

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["debug"])

        @router.post("/batch", response_model=CommandJob)
        async def send_request(req: DebugBatchRequest = Body(...)):
            return await self.send_batch_job(req)

        @router.post("/event/{job_id}", response_model=JobResponse)
        async def receive_event(job_id: str, req: str = Body(...)):
            return await self.event(job_id, req)

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
