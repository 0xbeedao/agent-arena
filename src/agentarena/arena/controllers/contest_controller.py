"""
ContestDTO controller for the Agent Arena application.
Handles HTTP requests for contest operations.
"""

from typing import Dict
from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from sqlmodel import Field

from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.models.contest import ContestDTO
from agentarena.models.contest import ContestRequest
from agentarena.models.contest import ContestState


class ContestController(ModelController[ContestDTO]):

    def __init__(
        self,
        base_path: str = "/api",
        model_service: ModelService[ContestDTO] = Field(
            description="The contest service"
        ),
        contest_factory: ContestFactory = Field(
            description="The contest builder factory"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.contest_factory = contest_factory
        super().__init__(
            base_path=base_path,
            model_service=model_service,
            model_name="contest",
            logging=logging,
        )

    # @router.post("/contest", response_model=Dict[str, str])
    async def create_contest(
        self,
        createRequest: ContestRequest,
    ) -> ContestDTO:
        """
        Create a new contest.

        Args:
            contest: The contest configuration
            model_service: The contest service

        Returns:
            A dictionary with the ID of the created contest
        """
        contestDTO = ContestDTO(
            arena_config_id=createRequest.arena_config_id,
            current_round=1,
            player_positions=";".join(createRequest.player_positions),
            state=ContestState.CREATED.value,
            start_time=None,
            end_time=None,
            winner=None,
        )
        contest, response = await self.model_service.create(contestDTO)
        if not response.success:
            raise HTTPException(status_code=422, detail=response.validation)

        # return await self.contest_factory.build(contest)
        return contest

    # @router.get("/contest/{contest_id}", response_model=Contest)
    async def get_contest(
        self,
        contest_id: str,
    ) -> ContestDTO:
        """
        Get a contest by ID.

        Args:
            contest_id: The ID of the contest to get

        Returns:
            The contest configuration

        Raises:
            HTTPException: If the contest is not found
        """
        contest, response = await self.model_service.get(contest_id)
        if not response.success:
            raise HTTPException(status_code=404, detail=response.error)
        return contest
        # return await self.contest_factory.build(contest_obj)

    # @router.put("/contest/{contest_id}", response_model=Dict[str, bool])
    async def update_contest(
        self,
        contest_id: str,
        contest: ContestDTO,
    ) -> Dict[str, bool]:
        """
        Update a contest.

        Args:
            contest_id: The ID of the contest to update
            contest: The new contest configuration
            model_service: The contest service

        Returns:
            A dictionary indicating success

        Raises:
            HTTPException: If the contest is not found
        """
        contest.winner = None
        response = await self.model_service.update(contest_id, contest)
        if not response.success:
            raise HTTPException(status_code=404, detail=response.validation)
        return {"success": response.success}

    # @router.post("/contest/{contest_id}/start", response_model=Dict[str, str])
    async def start_contest(
        self,
        contest_id: str,
    ) -> Dict[str, str]:
        """
        Start a contest, and returns the ID of the started contest, with everything set up for first round.

        Args:
            contest_id: The ID of the contest to start
            model_service: The contest service

        Returns:
            A dictionary with the ID of the started contest
        """
        boundlog = self.log.bind(contest_id=contest_id)
        boundlog.info("starting contest")
        contestDTO, response = await self.model_service.get(contest_id)
        if not response.success:
            boundlog.error("failed to get contest")
            raise HTTPException(status_code=404, detail=response.validation)

        if contestDTO.state != ContestState.CREATED:
            boundlog.error(f"contest is not in CREATED state, was: {contestDTO.state}")
            raise HTTPException(
                status_code=422, detail="Contest is not in CREATED state"
            )

        # sanity check, we need at least one player, announcer, judge, and participant
        contest = await self.contest_factory.build(contestDTO)
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
                boundlog.error(f"No agents in arena for role {role}, raising error")
                raise HTTPException(
                    status_code=422, detail=f"Arena needs at least one {role} agent"
                )

        # Set contest state to STARTING
        # and update start time
        # contestDTO.state = ContestStatus.STARTING
        # contestDTO.start_time = int(datetime.now().timestamp())
        # model_service.update(contest_id, contestDTO)

        # Populate the features if needed
        # if arena.max_random_features > 0:
        #     random_features = []

        return {"id": contest_id}

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=[self.model_name])

        @router.post("/", response_model=ContestDTO)
        async def create(req: ContestRequest = Body(...)):
            return await self.create_contest(req)

        @router.get("/{obj_id}", response_model=ContestDTO)
        async def get(obj_id: str):
            return await self.get_contest(obj_id)

        @router.get("", response_model=List[ContestDTO])
        async def list_all():
            return await self.get_model_list()

        @router.get("/list", response_model=List[ContestDTO])
        async def list_alias():
            return await self.get_model_list()

        @router.put("/", response_model=Dict[str, bool])
        async def update(req_id: str, req: ContestDTO = Body(...)):
            return await self.update_contest(req_id, req)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            return await self.delete_model(obj_id)

        return router
