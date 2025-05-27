"""
Responder controller for Agent Response endpoints
"""

from fastapi import APIRouter
from sqlmodel import Field, Session

from agentarena.arena.models import Participant, ParticipantCreate
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.models.job import JobResponseState
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus


class ResponderController:

    def __init__(
        self,
        base_path: str = "/api/responder",
        participant_service: ModelService[Participant, ParticipantCreate] = Field(
            description="the participant service"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.base_path = f"{base_path}/responder"
        self.participant_service = participant_service
        self.log = logging.get_logger("controller", path=self.base_path)

    async def healthcheck(
        self, participant_id: str, job_id: str, session: Session
    ) -> HealthResponse:
        p, response = await self.participant_service.get(participant_id, session)

        if not response.success or not p:
            return HealthResponse(
                state=JobResponseState.FAIL,
                message=f"no such responder: {participant_id}",
                job_id=job_id,
            )

        return HealthResponse(
            state=JobResponseState.COMPLETE,
            job_id=job_id,
            data=HealthStatus(name=p.name, state="OK", version="1"),
        )

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["Responders"])

        @router.get("/{participant_id}/health/{job_id}", response_model=HealthResponse)
        async def health(participant_id: str, job_id: str):
            with self.participant_service.db_service.get_session() as session:
                return await self.healthcheck(participant_id, job_id, session)

        return router
