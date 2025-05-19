"""
Responder controller for Agent Response endpoints
"""

from fastapi import APIRouter
from pydantic import Field

from agentarena.arena.factories.participant_factory import ParticipantFactory
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.models.participant import Participant
from agentarena.models.participant import ParticipantDTO
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus


class ResponderController:

    def __init__(
        self,
        base_path: str = "",  # NOT API - this is a logically separate service
        participant_factory: ParticipantFactory = Field(
            description="The participant factory"
        ),
        participant_service: ModelService[ParticipantDTO] = Field(
            description="the participant service"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.base_path = f"{base_path}/responder"
        self.participant_factory = participant_factory
        self.participant_service = participant_service
        self.log = logging.get_logger("controller", path=self.base_path)

    # @router.get(
    #    "/responders/{participant_id}/health/{job_id}", response_model=HealthResponse
    # )
    async def healthcheck(self, participant_id: str, job_id: str) -> HealthResponse:
        aa, response = await self.participant_service.get(participant_id)

        if not response.success:
            return HealthResponse(
                state="failed",
                message=f"no such responder: {participant_id}",
                job_id=job_id,
            )

        participant: Participant = await self.participant_factory.build(aa)

        return HealthResponse(
            state="completed",
            job_id=job_id,
            data=HealthStatus(name=participant.name, state="OK", version="1"),
        )

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["Responders"])

        @router.get("/{participant_id}/health/{job_id}", response_model=HealthResponse)
        async def health(participant_id: str, job_id: str):
            return await self.healthcheck(participant_id, job_id)

        return router
