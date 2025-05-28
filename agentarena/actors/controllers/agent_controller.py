"""
Responder controller for Agent Response endpoints
"""

from sqlmodel import Field
from sqlmodel import Session

from agentarena.actors.models import Agent
from agentarena.actors.models import AgentCreate
from agentarena.actors.models import AgentPublic
from agentarena.actors.models import AgentUpdate
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState
from agentarena.models.requests import HealthStatus


class AgentController(ModelController[Agent, AgentCreate, AgentUpdate, AgentPublic]):

    def __init__(
        self,
        base_path: str = "/api",
        agent_service: ModelService[Agent, AgentCreate] = Field(
            description="the participant service"
        ),
        uuid_service: UUIDService = Field(description="UUID Service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        super().__init__(
            base_path=base_path,
            model_name="agent",
            model_create=AgentCreate,
            model_update=AgentUpdate,
            model_public=AgentPublic,
            model_service=agent_service,
            logging=logging,
        )
        self.uuid_service = uuid_service

    async def healthcheck(self, agent_id: str, session: Session) -> JobResponse:
        agent, response = await self.model_service.get(agent_id, session)
        uuid = self.uuid_service.make_id()
        self.log.info(
            "healthcheck",
            agent_id=agent_id,
            participant=agent,
            uuid=uuid,
        )

        if not response.success or not agent:
            return JobResponse(
                channel="",
                state=JobResponseState.FAIL,
                message=f"no such responder: {agent_id}",
                job_id=uuid,
                data=HealthStatus(
                    name=agent_id,
                    state="FAIL",
                    version="1",
                ).model_dump(),
            )

        self.log.info("healthcheck complete", uuid=uuid)

        return JobResponse(
            channel="",
            state=JobResponseState.COMPLETE,
            message="OK",
            job_id=uuid,
            data=HealthStatus(name=agent.name, state="OK", version="1").model_dump(),
            url=f"{self.base_path}/{agent_id}/health",
        )

    def get_router(self):
        router = super().get_router()

        @router.get("/{agent_id}/health", response_model=JobResponse)
        async def health(agent_id: str):
            with self.model_service.db_service.get_session() as session:
                return await self.healthcheck(agent_id, session)

        return router
