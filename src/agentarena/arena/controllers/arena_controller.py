"""
Arena controller for the Agent Arena application.
Handles HTTP requests for arena operations.
"""

from typing import Dict
from typing import List

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from sqlmodel import Field, Session

from agentarena.arena.models.arena import Arena
from agentarena.arena.models.arena import ArenaCreate
from agentarena.arena.models.arena import ArenaPublic
from agentarena.arena.models.arena import ArenaUpdate
from agentarena.arena.models.arena import Feature
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService


class ArenaController(ModelController[Arena, ArenaCreate, ArenaUpdate, ArenaPublic]):

    def __init__(
        self,
        base_path: str = "/api",
        arena_service: ModelService[Arena] = Field(description="The arena service"),
        feature_service: ModelService[Feature] = Field(
            description="The feature service"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.feature_service = feature_service
        super().__init__(
            base_path=base_path,
            model_service=arena_service,
            model_public=ArenaPublic,
            model_name="arena",
            logging=logging,
        )

    async def create_arena(self, req: ArenaCreate, session: Session) -> Arena:
        """
        Create a new arena.

        Args:
            arena_config: The arena configuration

        Returns:
            The Arena
        """
        log = self.log.bind(method="create_arena", arena=req.name)
        features = []

        if req.features:
            features, errors = await self.feature_service.create_many(
                req.features, session  # type: ignore
            )

            if errors:
                session.rollback()
                raise HTTPException(status_code=422, detail=errors)

        arena, result = await self.model_service.create(req, session)
        if not result.success:
            raise HTTPException(status_code=422, detail=result)
        if not arena:
            raise HTTPException(status_code=422, detail="internal error")

        for f in features:
            arena.features.append(f)

        log.info(f"Created arena: {arena.id}")
        return arena

    def get_router(self):
        prefix = self.base_path
        if not prefix.endswith(self.model_name):
            prefix = f"{prefix}/arena"
        self.log.info("setting up routes", path=prefix)
        router = APIRouter(prefix=prefix, tags=["arena"])

        @router.post("/", response_model=Arena)
        async def create(req: ArenaCreate = Body(...)):
            with self.model_service.get_session() as session:
                return await self.create_arena(req, session)

        @router.get("/{obj_id}", response_model=Arena)
        async def get(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        @router.get("/", response_model=List[Arena])
        async def list_all():
            with self.model_service.get_session() as session:
                return await self.get_model_list(session)

        @router.get("/list", response_model=List[Arena])
        async def list_alias():
            with self.model_service.get_session() as session:
                return await self.get_model_list(session)

        @router.put("/", response_model=ArenaCreate)
        async def update(req_id: str, req: ArenaUpdate = Body(...)):
            with self.model_service.get_session() as session:
                return await self.update_model(req_id, req, session)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.delete_model(obj_id, session)

        return router
