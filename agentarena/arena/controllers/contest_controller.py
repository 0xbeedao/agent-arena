"""
ContestDTO controller for the Agent Arena application.
Handles HTTP requests for contest operations.
"""

from datetime import datetime
from typing import Dict
from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from sqlmodel import Field
from sqlmodel import Session

from agentarena.arena.models import Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import ContestPublic
from agentarena.arena.models import ContestState
from agentarena.arena.models import ContestUpdate
from agentarena.arena.models import Participant
from agentarena.arena.models import ParticipantCreate
from agentarena.arena.models import ParticipantRole
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService


class ContestController(
    ModelController[Contest, ContestCreate, ContestUpdate, ContestPublic]
):

    def __init__(
        self,
        base_path: str = "/api",
        model_service: ModelService[Contest, ContestCreate] = Field(
            description="The contest service"
        ),
        participant_service: ModelService[Participant, ParticipantCreate] = Field(
            description="The feature service"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.participant_service = participant_service
        super().__init__(
            base_path=base_path,
            model_service=model_service,
            model_public=ContestPublic,
            model_name="contest",
            logging=logging,
        )

    # @router.post("/contest", response_model=Dict[str, str])
    async def create_contest(self, req: ContestCreate, session: Session) -> Contest:
        """
        Create a new contest.

        Args:
            contest: The contest configuration
            model_service: The contest service

        Returns:
            A dictionary with the ID of the created contest
        """
        if not req.participant_ids:
            raise HTTPException(status_code=422, detail="Need at least 1 participant")

        participants = await self.participant_service.get_by_ids(
            req.participant_ids, session
        )

        if len(participants) != len(req.participant_ids):
            session.rollback()
            raise HTTPException(
                status_code=422, detail="Could not get all participants"
            )

        contest, result = await self.model_service.create(req, session)
        if not result.success:
            raise HTTPException(status_code=422, detail=result.model_dump_json())
        if not contest:
            raise HTTPException(status_code=422, detail="internal error")

        for p in participants:
            contest.participants.append(p)

        # session.commit() # needed?
        return contest

    # @router.post("/contest/{contest_id}/start", response_model=Dict[str, str])
    async def start_contest(self, contest_id: str, session: Session) -> Dict[str, str]:
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
        contest, response = await self.model_service.get(contest_id, session)
        if not response.success:
            boundlog.error("failed to get contest")
            raise HTTPException(status_code=404, detail=response.validation)
        if not contest:
            boundlog.error("failed to get contest data")
            raise HTTPException(status_code=404, detail="internal error")

        if contest.state != ContestState.CREATED.value:
            boundlog.error(f"contest is not in CREATED state, was: {contest.state}")
            raise HTTPException(
                status_code=422, detail="Contest is not in CREATED state"
            )

        participants = [p for p in contest.participants]
        if len(participants) < 4:
            boundlog.error("No agents in arena, raising error")
            raise HTTPException(
                status_code=422,
                detail="Arena needs at least 4 agents: player, announcer, judge, and participant",
            )

        roles = contest.participants_by_role()

        for role in ParticipantRole:
            key = role.value
            if roles[key] is None or len(roles[key]) == 0:
                boundlog.error(f"No agents in arena for role {key}, raising error")
                raise HTTPException(
                    status_code=422, detail=f"Arena needs at least one {key} agent"
                )

        # sanity check done, let's start

        # Set contest state to STARTING
        # and update start time
        contest.state = ContestState.STARTING.value
        contest.start_time = int(datetime.now().timestamp())
        await self.model_service.update(contest_id, contest, session)

        return {"id": contest_id}

    def get_router(self):
        prefix = self.base_path
        if not prefix.endswith(self.model_name):
            prefix = f"{prefix}/contest"
        self.log.info("setting up routes", path=prefix)
        router = APIRouter(prefix=prefix, tags=["arena"])

        @router.post("/", response_model=Contest)
        async def create(req: ContestCreate = Body(...)):
            with self.model_service.get_session() as session:
                return await self.create_contest(req, session)

        @router.get("/{obj_id}", response_model=Contest)
        async def get(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        @router.get("", response_model=List[Contest])
        async def list_all():
            with self.model_service.get_session() as session:
                return await self.get_model_list(session)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.delete_model(obj_id, session)

        return router
