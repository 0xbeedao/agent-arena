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
from agentarena.factories.contest_factory import ContestFactory
from agentarena.models.contest import Contest
from agentarena.models.contest import ContestDTO
from agentarena.models.contest import ContestRequest
from agentarena.models.contest import ContestStatus
from agentarena.models.participant import ParticipantRole
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
    make_participant=Callable[[ContestDTO], Awaitable[Contest]],
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
    contest_factory: ContestFactory = Depends(Provide(Container.contest_factory)),
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

    return await contest_factory.build(contest_obj)


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
    contest_factory=Depends(Provide[Container.contest_factory]),
    logging=Depends(Provide[Container.logging]),
) -> Dict[str, str]:
    """
    Start a contest, and returns the ID of the started contest, with everything set up for first round.

    Args:
        contest_id: The ID of the contest to start
        contest_service: The contest service

    Returns:
        A dictionary with the ID of the started contest
    """
    boundlog = logging.get_logger(contest_id=contest_id)
    boundlog.info("starting contest")
    [contestDTO, response] = await contest_service.get(contest_id)
    if not response.success:
        boundlog.error("failed to get contest")
        raise HTTPException(status_code=404, detail=response.validation)

    if contestDTO.status != ContestStatus.CREATED:
        boundlog.error("contest is not in CREATED state, was: %s", contestDTO.status)
        raise HTTPException(status_code=422, detail="Contest is not in CREATED state")

    # sanity check, we need at least one player, announcer, judge, and participant
    contest = await contest_factory.build(contestDTO)
    arena = contest.arena

    if arena.agents is None or len(arena.agents) < 4:
        boundlog.error("No agents in arena, raising error")
        raise HTTPException(
            status_code=422,
            detail="Arena needs at least 4 agents: player, announcer, judge, and participant",
        )

    agent_roles = arena.agents_by_role()

    for role in ParticipantRole:
        if agent_roles[role] is None or len(agent_roles[role]) == 0:
            boundlog.error("No agents in arena for role %s, raising error", role)
            raise HTTPException(
                status_code=422, detail=f"Arena needs at least one {role} agent"
            )

        agent_roles = arena.agents_by_role()

        for role in ParticipantRole:
            if agent_roles[role] is None or len(agent_roles[role]) == 0:
                boundlog.error("No agents in arena for role %s, raising error", role)
                raise HTTPException(
                    status_code=422, detail=f"Arena needs at least one {role} agent"
                )

        # Set contest status to STARTING
        # and update start time
        # contestDTO.status = ContestStatus.STARTING
        # contestDTO.start_time = int(datetime.now().timestamp())
        # model_service.update(contest_id, contestDTO)

        # Populate the features if needed
        # if arena.max_random_features > 0:
        #     random_features = []

        return {"id": contest_id}

    async def get_router(self):
        router = APIRouter(prefix=f"/{self.model_name}", tags=[self.model_name])

        @router.post("/", response_model=Contest)
        async def create(req: ContestDTO):
            return await self.create_contest(req)

        @router.get("/{obj_id}", response_model=Contest)
        async def get(obj_id: str):
            return await self.get_contest(obj_id)

        @router.get("/", response_model=List[ContestDTO])
        async def list_all():
            return await self.get_model_list()

        @router.get("/list", response_model=List[ContestDTO])
        async def list_alias():
            return await self.get_model_list()

        @router.put("/", response_model=Dict[str, bool])
        async def update(req_id: str, req: ContestDTO):
            return await self.update_contest(req_id, req)

    # Populate the features if needed
    # if arena.max_random_features > 0:
    #     random_features = []

    return {"id": contest_id}
