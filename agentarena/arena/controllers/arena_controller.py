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
from sqlmodel import Session

from agentarena.arena.models import Arena
from agentarena.arena.models import ArenaCreate
from agentarena.arena.models import ArenaUpdate
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import FeatureOriginType
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.models.public import ArenaPublic


class ArenaController(ModelController[Arena, ArenaCreate, ArenaUpdate, ArenaPublic]):

    def __init__(
        self,
        base_path: str = "/api",
        arena_service: ModelService[Arena, ArenaCreate] = Field(
            description="The arena service"
        ),
        feature_service: ModelService[Feature, FeatureCreate] = Field(
            description="The feature service"
        ),
        template_service: JinjaRenderer = Field(description="The template service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        self.feature_service = feature_service
        super().__init__(
            base_path=base_path,
            model_service=arena_service,
            model_public=ArenaPublic,
            model_name="arena",
            template_service=template_service,
            logging=logging,
        )

    async def create_arena(self, req: ArenaCreate, session: Session) -> ArenaPublic:
        """
        Create a new arena.

        Args:
            arena_config: The arena configuration

        Returns:
            The Arena
        """
        log = self.log.bind(method="create_arena", arena=req.name)
        features = req.features
        req.features = []
        arena, result = await self.model_service.create(req, session)
        if not result.success:
            raise HTTPException(status_code=422, detail=result.model_dump())
        if not arena:
            raise HTTPException(status_code=422, detail="internal error")

        log = log.bind(arena_id=arena.id)

        for f in features:
            feature = Feature(
                id="",
                name=f.name,
                description=f.description,
                position=f.position,
                # end_position=f.end_position,
                origin=f.origin or FeatureOriginType.REQUIRED,
            )
            log.info("Creating feature")
            feature, result = await self.feature_service.create(feature, session)
            if not result.success:
                raise HTTPException(status_code=422, detail=result.model_dump())
            if not feature:
                raise HTTPException(status_code=422, detail="internal error")
            arena.features.append(feature)

        session.commit()

        log.info(f"Created arena: {arena.id}")
        return arena.get_public()

    def get_router(self):
        prefix = self.base_path
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
