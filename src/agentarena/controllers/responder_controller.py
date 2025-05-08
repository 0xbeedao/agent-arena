"""
Responder controller for Agent Response endpoints
"""

from fastapi import APIRouter
from fastapi import Depends
from pydantic import Field

from agentarena.factories.participant_factory import ParticipantFactory
from agentarena.models.participant import Participant
from agentarena.models.participant import ParticipantDTO
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus
from agentarena.services.model_service import ModelService


class ResponderController:

    def __init__(
        self,
        participant_factory: ParticipantFactory = Field(
            description="The participant factory"
        ),
        participant_service: ModelService[ParticipantDTO] = Field(
            description="the participant service"
        ),
        logging=None,
    ):
        self.participant_factory = participant_factory
        self.participant_service = participant_service
        self.log = logging.get_logger(module="responder_controller")

    # @router.get(
    #    "/responders/{participant_id}/health/{job_id}", response_model=HealthResponse
    # )
    async def healthcheck(self, participant_id: str, job_id: str) -> HealthResponse:
        log = self.log.bind(participant_id=participant_id)
        aa, response = await self.participant_service.get(participant_id)

        if not response.success:
            return HealthResponse(
                state="failed",
                message=f"no such responder: #{participant_id}",
                job_id=job_id,
            )

        participant: Participant = await self.participant_factory.build(aa)

        return HealthResponse(
            state="completed",
            job_id=job_id,
            data=HealthStatus(name=participant.name, state="OK", version="1"),
        )

    def get_router(self):

        router = APIRouter(prefix="/responders", tags="Responders")

        @router.get("/{participant_id}/health/{job_id}", response_model=HealthResponse)
        async def health():
            return await self.healthcheck()

        return router
