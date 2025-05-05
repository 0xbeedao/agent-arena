"""
Responder controller for Agent Response endpoints
"""

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from fastapi import APIRouter
from fastapi import Depends

from agentarena.containers import Container
from agentarena.models.arenaagent import ArenaAgent
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.requests import HealthResponse
from agentarena.models.requests import HealthStatus
from agentarena.services.model_service import ModelService

# Create a router for agent endpoints
router = APIRouter(tags=["Responder"])


@router.get(
    "/responders/{arenaagent_id}/health/{job_id}", response_model=HealthResponse
)
@inject
async def healthcheck(
    arenaagent_id: str,
    job_id: str,
    arenaagent_service: ModelService[ArenaAgentDTO] = Depends(
        Provide[Container.arenaagent_service]
    ),
    logging=Depends(Provide[Container.logging]),
    arenaagent_factory=Depends(Provide[Container.arenaagent_factory]),
) -> HealthResponse:
    log = logging.get_logger("healthcheck")
    log.info(f"make_arenaagent: {arenaagent_service}")
    aa, response = await arenaagent_service.get(arenaagent_id)

    if not response.success:
        return HealthResponse(
            status="failed",
            message=f"no such responder: #{arenaagent_id}",
            job_id=job_id,
        )

    agent: ArenaAgent = await arenaagent_factory.build(aa)

    return HealthResponse(
        status="completed",
        job_id=job_id,
        data=HealthStatus(name=agent.name, status="OK", version="1"),
    )
