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

        with self.model_service.get_session() as session:

            if req.features:
                features, errors = await self.feature_service.create_many(
                    req.features, session
                )

                if errors:
                    session.rollback()
                    raise HTTPException(status_code=422, detail=errors)

            if not req.participants:
                raise HTTPException(
                    status_code=422, detail="Need at least 1 participant"
                )

            participants, errors = await self.participant_service.get_by_ids(
                req.participants, session
            )

            if errors:
                session.rollback()
                raise HTTPException(status_code=422, detail=errors)

        # # get and validate the features
        # invalid_features = await self.feature_service.validate_list(features)
        # if invalid_features:
        #     for invalidation in invalid_features:
        #         log.info(f"Invalid: {invalidation.model_dump_json()}")
        #     raise HTTPException(
        #         status_code=422, detail=invalid_features[0].validation.model_dump_json()
        #     )

        # # repeat for agents
        # agent_ids = [agent.agent_id for agent in agents]
        # _, problems = await self.agent_service.get_by_ids(agent_ids)
        # if problems:
        #     for problem in problems:
        #         log.info("Invalid agent", json=problem.model_dump_json())
        #     raise HTTPException(status_code=422, detail=problems[0].model_dump_json())

        # # create the new arena
        # [arena, response] = await self.model_service.create(arenaDTO)
        # if not response.success:
        #     log.info(
        #         "Failed to create arena", json=response.validation.model_dump_json()
        #     )
        #     raise HTTPException(
        #         status_code=422, detail=response.validation.model_dump_json()
        #     )

        # # Map the features to the arena
        # if (len(features) + len(agents)) > 0:
        #     response = await self.add_features_and_agents(arena.id, createRequest)
        #     if not response.success:
        #         log.info(
        #             "Failed to map features and agents",
        #             response=response.validation.model_dump_json(),
        #         )
        #         raise HTTPException(
        #             status_code=422, detail=response.validation.model_dump_json()
        #         )

        log.info(f"Created arena: {arena.id}")
        return arena
        # If we get here, the arena was created successfully
        # return await self.arena_factory.build(arena)

    # @router.get("/arena/{arena_id}", response_model=Arena)
    async def get_arena(
        self,
        arena_id: str,
    ) -> Arena:
        """
        Get an arena by ID.

        Args:
            arena_id: The ID of the arena to get

        Returns:
            The arena configuration

        Raises:
            HTTPException: If the arena is not found
        """
        arenaDTO, response = await self.get_model(arena_id)
        if not response.success:
            raise HTTPException(status_code=404, detail=response.error)

        # return await self.arena_factory.build(arenaDTO)
        return arenaDTO

    # @router.put("/arena/{arena_id}", response_model=Dict[str, bool])
    async def update_arena(
        self,
        arena_id: str,
        updateRequest: ArenaCreate,
    ) -> Arena:
        """
        Update an arena.

        Args:
            arena_id: The ID of the arena to update
            arena_config: The new arena configuration

        Returns:
            the updated Arena

        Raises:
            HTTPException: If the arena is not found
        """
        features = updateRequest.features
        agents = updateRequest.agents
        log = self.log.bind(method="update_arena", arena_id=arena_id)

        # get and validate the features
        invalid_features = await self.feature_service.validate_list(features)
        if invalid_features:
            for invalidation in invalid_features:
                log.info("Invalid", invalidation=invalidation.model_dump_json())
            raise HTTPException(
                status_code=422, detail=invalid_features[0].validation.model_dump_json()
            )

        # repeat for agents
        agent_ids = [agent.agent_id for agent in agents]
        _, problems = await self.agent_service.get_by_ids(agent_ids)
        if problems:
            for problem in problems:
                log.info(f"Invalid agent: {problem.model_dump_json()}")
            raise HTTPException(status_code=422, detail=problems[0].model_dump_json())

        arena_config = Arena(
            id=arena_id,
            name=updateRequest.name,
            description=updateRequest.description,
            height=updateRequest.height,
            width=updateRequest.width,
            rules=updateRequest.rules,
            max_random_features=updateRequest.max_random_features,
            winning_condition=updateRequest.winning_condition,
        )
        arenaDTO, response = await self.model_service.update(arena_config)
        if not response.success:
            log.info(
                f"Failed to update arena: {response.validation.model_dump_json()}",
            )
            raise HTTPException(status_code=422, detail=response.validation)

        # Add new mappings
        response = await self.add_features_and_agents(
            arena_id, updateRequest, features, agents, clean=True
        )
        if not response.success:
            log.info(
                f"Failed to map features and agents: {response.validation.model_dump_json()}"
            )
            raise HTTPException(status_code=422, detail=response.validation)

        log.info("Updated arena")
        # return self.arena_factory.build(arenaDTO)
        return arenaDTO

    async def add_features_and_agents(
        self,
        arena_id: str,
        createRequest: ArenaCreate,
        clean: bool = False,
    ) -> ModelResponse:
        """
        Add features and agents to the arena.

        Args:
            createRequest: The arena creation request
            features: The list of features to add
            agents: The list of agents to add
        """
        locallog = self.log.bind(
            arena_id=arena_id,
            method="add_features_and_agents",
        )
        # If clean is true, delete the existing features and agents
        if clean:
            locallog.info("Deleting old features and agents")
            self.feature_service.table.delete_where(
                "arena_config_id = :id", {"id": arena_id}
            )
            self.participant_service.table.delete_where(
                "arena_config_id = :id", {"id": arena_id}
            )

        features = createRequest.features
        agents = createRequest.agents
        # db.execute("BEGIN TRANSACTION")
        boundlog = locallog.bind(featureCt=len(features), agentCt=len(agents))
        boundlog.info("Mapping features and agents to arena")
        if len(features) > 0:

            feature_objects = [
                Feature(
                    name=featureReq.name,
                    description=featureReq.description,
                    position=featureReq.position,
                    end_position=featureReq.end_position,
                    arena_config_id=arena_id,
                    origin=FeatureOriginType.REQUIRED.value,
                )
                for featureReq in createRequest.features
            ]

            _, problems = await self.feature_service.create_many(feature_objects)
            if problems:
                boundlog.error(f"Failed to map features to arena, rolling-back")
                # db.execute("ROLLBACK")
                return problems[0]

        locallog.debug(f"Mapped {len(features)} features to arena")

        # Map the agents to the arena
        if len(agents) > 0:
            for agentReq in agents:
                participant = ParticipantDTO(
                    arena_config_id=arena_id,
                    agent_id=agentReq.agent_id,
                    role=agentReq.role,
                )
                [_, response] = await self.participant_service.create(participant)
                if not response.success:
                    boundlog.error(
                        f"Failed to map agent {agentReq.id} to arena, rolling-back",
                    )
                    # db.execute("ROLLBACK")
                    return ModelResponse(success=False, validation=response.validation)
        locallog.debug(f"Mapped {len(agents)} agents to arena")

        # db.execute("COMMIT")
        return ModelResponse(success=True)

    def get_router(self):
        self.log.info("getting router")
        router = APIRouter(prefix=self.base_path, tags=["arena"])

        @router.post("/", response_model=Arena)
        async def create(req: ArenaCreate = Body(...)):
            return await self.create_arena(req)

        @router.get("/{obj_id}", response_model=Arena)
        async def get(obj_id: str):
            return await self.get_arena(obj_id)

        @router.get("/", response_model=List[Arena])
        async def list_all():
            return await self.get_model_list()

        @router.get("/list", response_model=List[Arena])
        async def list_alias():
            return await self.get_model_list()

        @router.put("/", response_model=ArenaCreate)
        async def update(req_id: str, req: ArenaCreate = Body(...)):
            return await self.update_arena(req_id, req)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            return await self.delete_model(obj_id)

        return router
