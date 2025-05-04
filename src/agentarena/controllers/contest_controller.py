"""
ContestDTO controller for the Agent Arena application.
Handles HTTP requests for contest operations.
"""

from typing import Awaitable
from typing import Callable
from typing import Dict
from typing import List

from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from agentarena.containers import Container
from agentarena.models.arenaagent import AgentRole
from agentarena.models.contest import Contest
from agentarena.models.contest import ContestDTO
from agentarena.models.contest import ContestRequest
from agentarena.models.contest import ContestStatus
from agentarena.services.model_service import ModelService

# Create a router for contest endpoints
router = APIRouter(tags=["ContestDTO"])


@router.post("/contest", response_model=Dict[str, str])
@inject
async def create_contest(
    createRequest: ContestRequest,
    contest_service: ModelService[ContestDTO] = Depends(
        Provide[Container.contest_service]
    ),
    make_arenaagent=Callable[[ContestDTO], Awaitable[Contest]],
) -> Dict[str, str]:
    """
    Create a new contest.

    Args:
        contest: The contest configuration
        contest_service: The contest service

    Returns:
        A dictionary with the ID of the created contest
    """
    contestDTO = ContestDTO(
        arena_config_id=createRequest.arena_config_id,
        current_round=1,
        player_positions=";".join(createRequest.player_positions),
        status=ContestStatus.CREATED.value,
        start_time=None,
        end_time=None,
        winner=None,
    )
    [contest_id, response] = await contest_service.create(contestDTO)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)

    return {"id": contest_id}


@router.get("/contest/{contest_id}", response_model=Contest)
@inject
async def get_contest(
    contest_id: str,
    contest_service: ModelService[ContestDTO] = Depends(
        Provide[Container.contest_service]
    ),
) -> Contest:
    """
    Get a contest by ID.

    Args:
        contest_id: The ID of the contest to get
        contest_service: The contest service

    Returns:
        The contest configuration

    Raises:
        HTTPException: If the contest is not found
    """
    [contest_obj, response] = await contest_service.get(contest_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)

    return await make_contest(contest_obj)


@router.get("/contest", response_model=List[ContestDTO])
@inject
async def get_contest_list(
    contest_service: ModelService[ContestDTO] = Depends(
        Provide[Container.contest_service]
    ),
) -> List[ContestDTO]:
    """
    Get a list of all contests.

    Args:
        contest_service: The contest service

    Returns:
        A list of contest configurations
    """
    return await contest_service.list()


@router.put("/contest/{contest_id}", response_model=Dict[str, bool])
@inject
async def update_contest(
    contest_id: str,
    contest: ContestDTO,
    contest_service: ModelService[ContestDTO] = Depends(
        Provide[Container.contest_service]
    ),
) -> Dict[str, bool]:
    """
    Update a contest.

    Args:
        contest_id: The ID of the contest to update
        contest: The new contest configuration
        contest_service: The contest service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the contest is not found
    """
    contest.winner = None
    response = await contest_service.update(contest_id, contest)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.validation)
    return {"success": response.success}


@router.delete("/contest/{contest_id}", response_model=Dict[str, bool])
@inject
async def delete_contest(
    contest_id: str,
    contest_service: ModelService[ContestDTO] = Depends(
        Provide[Container.contest_service]
    ),
) -> Dict[str, bool]:
    """
    Delete a contest.

    Args:
        contest_id: The ID of the contest to delete
        contest_service: The contest service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the contest is not found
    """
    response = await contest_service.delete(contest_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.validation)
    return {"success": response.success}


@router.post("/contest/{contest_id}/start", response_model=Dict[str, str])
@inject
async def start_contest(
    contest_id: str,
    contest_service: ModelService[ContestDTO] = Depends(
        Provide[Container.contest_service]
    ),
    make_logger=Depends(Provide[Container.make_logger]),
) -> Dict[str, str]:
    """
    Start a contest, and returns the ID of the started contest, with everything set up for first round.

    Args:
        contest_id: The ID of the contest to start
        contest_service: The contest service

    Returns:
        A dictionary with the ID of the started contest
    """
    boundlog = make_logger(contest_id=contest_id)
    boundlog.info("starting contest")
    [contestDTO, response] = await contest_service.get(contest_id)
    if not response.success:
        boundlog.error("failed to get contest")
        raise HTTPException(status_code=404, detail=response.validation)

    if contestDTO.status != ContestStatus.CREATED:
        boundlog.error("contest is not in CREATED state, was: %s", contestDTO.status)
        raise HTTPException(status_code=422, detail="Contest is not in CREATED state")

    # sanity check, we need at least one player, announcer, judge, and arena agent
    contest = await make_contest(contestDTO)
    arena = contest.arena

    if arena.agents is None or len(arena.agents) < 4:
        boundlog.error("No agents in arena, raising error")
        raise HTTPException(
            status_code=422,
            detail="Arena needs at least 4 agents: player, announcer, judge, and arena agent",
        )

    agent_roles = arena.agents_by_role()

    for role in AgentRole:
        if agent_roles[role] is None or len(agent_roles[role]) == 0:
            boundlog.error("No agents in arena for role %s, raising error", role)
            raise HTTPException(
                status_code=422, detail=f"Arena needs at least one {role} agent"
            )

    # Set contest status to STARTING
    # and update start time
    # contestDTO.status = ContestStatus.STARTING
    # contestDTO.start_time = datetime.now()
    # contest_service.update(contest_id, contestDTO)

    # Populate the features if needed
    # if arena.max_random_features > 0:
    #     random_features = []

    return {"id": contest_id}
