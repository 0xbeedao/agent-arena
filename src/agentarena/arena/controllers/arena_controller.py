"""
Arena controller for the Agent Arena application.
Handles HTTP requests for arena operations.
"""

from typing import Dict
from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from sqlmodel import Field

from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelResponse
from agentarena.core.services.model_service import ModelService
from agentarena.models.arena import (
    Arena,
    ArenaPublic,
    ArenaUpdate,
    Feature,
    Participant,
)
from agentarena.models.arena import ArenaCreate


class ArenaController(ModelController[Arena, ArenaCreate, ArenaUpdate, ArenaPublic]):

    def __init__(
        self,
        base_path: str = "/api",
        arena_service: ModelService[Arena] = Field(description="The arena service"),
        feature_service: ModelService[Feature] = Field(
            description="The feature service"
        ),
        participant_service: ModelService[Participant] = Field(
            description="The feature service"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.feature_service = feature_service
        self.participant_service = participant_service
        super().__init__(
            base_path=base_path,
            model_service=arena_service,
            model_public=ArenaPublic,
            model_name="arena",
            logging=logging,
        )

    # @router.post("/arena", response_model=Arena)
    async def create_arena(
        self,
        req: ArenaCreate,
    ) -> Arena:
        """
        Create a new arena.

        Args:
            arena_config: The arena configuration

        Returns:
            The Arena
        """
        log = self.log.bind(method="create_arena", arena=req.name)
        features = []
        participants = []

        with self.model_service.get_session() as session:

            if req.features:
                features, errors = await self.feature_service.create_many(
                    req.features, session  # type: ignore
                )

                if errors:
                    session.rollback()
                    raise HTTPException(status_code=422, detail=errors)

            if not req.participants:
                raise HTTPException(
                    status_code=422, detail="Need at least 1 participant"
                )

            participants = await self.participant_service.get_by_ids(
                req.participants, session
            )

            if len(participants) != len(req.participants):
                session.rollback()
                raise HTTPException(
                    status_code=422, detail="Could not get all participants"
                )

            arena, problem = await self.model_service.create(req, session)
            if problem:
                raise HTTPException(status_code=422, detail=problem)
            if not arena:
                raise HTTPException(status_code=422, detail="internal error")

            for p in participants:
                arena.participants.append(p)

            for f in features:
                arena.features.append(f)

            session.commit()
        log.info(f"Created arena: {arena.id}")
        return arena

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["arena"])

        @router.post("/", response_model=Arena)
        async def create(req: ArenaCreate = Body(...)):
            return await self.create_arena(req)

        @router.get("/{obj_id}", response_model=Arena)
        async def get(obj_id: str):
            return await self.get_model(obj_id)

        @router.get("/", response_model=List[Arena])
        async def list_all():
            return await self.get_model_list()

        @router.get("/list", response_model=List[Arena])
        async def list_alias():
            return await self.get_model_list()

        @router.put("/", response_model=ArenaCreate)
        async def update(req_id: str, req: ArenaUpdate = Body(...)):
            return await self.update_model(req_id, req)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            return await self.delete_model(obj_id)

        return router
