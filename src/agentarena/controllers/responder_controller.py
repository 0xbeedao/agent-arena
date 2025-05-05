"""
Responder controller for Agent Response endpoints
"""

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from fastapi import APIRouter
from fastapi import Depends

from agentarena.containers import Container
from agentarena.models.participant import Participant
from agentarena.models.participant import ParticipantDTO
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus
from agentarena.services.model_service import ModelService

# Create a router for agent endpoints
router = APIRouter(tags=["Responder"])


@router.get(
    "/responders/{participant_id}/health/{job_id}", response_model=HealthResponse
)
@inject
async def healthcheck(
    participant_id: str,
    job_id: str,
    participant_service: ModelService[ParticipantDTO] = Depends(
        Provide[Container.participant_service]
    ),
    logging=Depends(Provide[Container.logging]),
    participant_factory=Depends(Provide[Container.participant_factory]),
) -> HealthResponse:
    log = logging.get_logger("healthcheck")
    log.info(f"make_participant: {participant_service}")
    aa, response = await participant_service.get(participant_id)

    if not response.success:
        return HealthResponse(
            status="failed",
            message=f"no such responder: #{participant_id}",
            job_id=job_id,
        )

    agent: Participant = await participant_factory.build(aa)

    return HealthResponse(
        status="completed",
        job_id=job_id,
        data=HealthStatus(name=agent.name, status="OK", version="1"),
    )
