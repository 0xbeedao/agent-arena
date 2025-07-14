from fastapi import APIRouter
from nats.aio.client import Client as NatsClient
from sqlmodel import Field

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.constants import JobResponseState
from agentarena.models.public import JobResponse
from agentarena.models.requests import HealthStatus


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

    async def healthOK(self):
        self.log.info("health OK")
        return JobResponse(
            job_id="1",
            state=JobResponseState.COMPLETE,
            message="test",
            data=HealthStatus(
                name="debug_controller", state="OK", version="1"
            ).model_dump_json(),
        )

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["debug"])

        @router.get("/health", response_model=JobResponse)
        async def health():
            return await self.healthOK()

        return router
