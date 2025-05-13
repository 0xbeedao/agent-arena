from datetime import datetime

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.agent import AgentDTO
from agentarena.models.job import CommandJob
from agentarena.models.job import JobCommandType
from agentarena.models.job import JobResponseState
from agentarena.models.job import JobState
from agentarena.models.job import JsonRequestSummary
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService


class DebugController:
    """
    Provides debug/raw endpoints for testing and discovery.
    """

    def __init__(
        self,
        base_path: str = "/api",
        agent_service: ModelService[AgentDTO] = Field(
            description="The Agent DTO Service"
        ),
        queue_service: QueueService = Field(description="queue service"),
        job_service: ModelService[CommandJob] = Field(description="Job Model service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.agent_service = agent_service
        self.base_path = f"{base_path}/debug"
        self.job_service = job_service
        self.q = queue_service
        self.log = logging.get_logger("controller", path=self.base_path)

    async def get_job(self, job_id: str = Field(description="job ID to fetch")):
        job, response = await self.job_service.get(job_id)
        if not response.success:
            raise HTTPException(status_code="404", detail=job_id)
        return job

    async def send_request_job(self, req: JsonRequestSummary) -> CommandJob:
        job = CommandJob(
            command=JobCommandType.REQUEST.value,
            data=req.data,
            event=req.event,
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

        @router.get("/job/{job_id}", response_model=CommandJob)
        async def get_job(job_id: str):
            return await self.get_job(job_id)

        @router.post("/request", response_model=CommandJob)
        async def send_request(req: JsonRequestSummary = Body(...)):
            return await self.send_request_job(req)

        @router.get("/health", response_model=HealthResponse)
        async def health():
            return await self.healthOK()

        return router
