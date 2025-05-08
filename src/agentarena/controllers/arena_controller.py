"""
Arena controller for the Agent Arena application.
Handles HTTP requests for arena operations.
"""

from typing import Dict
from typing import List
from typing import Tuple

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import Field

from agentarena.controllers.model_controller import ModelController
from agentarena.factories.arena_factory import ArenaFactory
from agentarena.models.agent import AgentDTO
from agentarena.models.arena import Arena
from agentarena.models.arena import ArenaCreateRequest
from agentarena.models.arena import ArenaDTO
from agentarena.models.dbbase import DbBase
from agentarena.models.feature import FeatureDTO
from agentarena.models.feature import FeatureOriginType
from agentarena.models.participant import ParticipantDTO
from agentarena.services.model_service import ModelResponse
from agentarena.services.model_service import ModelService


class ArenaController(ModelController[ArenaDTO]):

    def __init__(
        self,
        model_service: ModelService[ArenaDTO] = Field(description="The arena service"),
        agent_service: ModelService[AgentDTO] = Field(description="The agent service"),
        feature_service: ModelService[FeatureDTO] = Field(
            Description="The feature service"
        ),
        participant_service: ModelService[ParticipantDTO] = Field(
            description="The participant service"
        ),
        arena_factory: ArenaFactory = Field(description="The arena builder factory"),
        logging=None,
    ):
        self.agent_service = agent_service
        self.arena_factory = arena_factory
        self.feature_service = feature_service
        self.participant_service = participant_service
        super().__init__(
            model_service=model_service, model_name="arena", logging=logging
        )

    # @router.post("/arena", response_model=Arena)
    async def create_arena(
        self,
        createRequest: ArenaCreateRequest,
    ) -> Arena:
        """
        Create a new arena.

        Args:
            arena_config: The arena configuration

        Returns:
            The Arena
        """
        arenaDTO = ArenaDTO(
            name=createRequest.name,
            description=createRequest.description,
            height=createRequest.height,
            width=createRequest.width,
            rules=createRequest.rules,
            max_random_features=createRequest.max_random_features,
            winning_condition=createRequest.winning_condition,
        )

        features = createRequest.features
        agents = createRequest.agents
        log = self.log.bind(method="create_arena", arena=arenaDTO.name)

        # get and validate the features
        invalid_features = get_invalid_features(features)
        if invalid_features:
            for invalidation in invalid_features:
                log.info("Invalid: %s", invalidation.model_dump_json())
            raise HTTPException(
                status_code=422, detail=invalid_features[0].validation.model_dump_json()
            )

        # repeat for agents
        agent_ids = [agent.agent_id for agent in agents]
        _, problems = await self.agent_service.get_by_ids(agent_ids)
        if problems:
            for problem in problems:
                log.info("Invalid agent: %s", problem.model_dump_json())
            raise HTTPException(status_code=422, detail=problems[0].model_dump_json())

        # create the new arena
        [arena, response] = await self.model_service.create(arenaDTO)
        if not response.success:
            log.info(
                "Failed to create arena: %s", response.validation.model_dump_json()
            )
            raise HTTPException(
                status_code=422, detail=response.validation.model_dump_json()
            )

        # Map the features to the arena
        if (len(features) + len(agents)) > 0:
            response = await self.add_features_and_agents(
                arena.id, createRequest, log=log
            )
            if not response.success:
                log.info(
                    "Failed to map features and agents: %s",
                    response.validation.model_dump_json(),
                )
                raise HTTPException(
                    status_code=422, detail=response.validation.model_dump_json()
                )

        log.info("Created arena: %s", arena.id)
        # If we get here, the arena was created successfully
        return await self.arena_factory.build(arena)

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

        return await self.arena_factory.build(arenaDTO)

    # @router.put("/arena/{arena_id}", response_model=Dict[str, bool])
    async def update_arena(
        self,
        arena_id: str,
        updateRequest: ArenaCreateRequest,
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
        invalid_features = get_invalid_features(features)
        if invalid_features:
            for invalidation in invalid_features:
                log.info("Invalid: %s", invalidation.model_dump_json())
            raise HTTPException(
                status_code=422, detail=invalid_features[0].validation.model_dump_json()
            )

        # repeat for agents
        agent_ids = [agent.agent_id for agent in agents]
        _, problems = await self.agent_service.get_by_ids(agent_ids)
        if problems:
            for problem in problems:
                log.info("Invalid agent: %s", problem.model_dump_json())
            raise HTTPException(status_code=422, detail=problems[0].model_dump_json())

        arena_config = ArenaDTO(
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
                "Failed to update arena: %s", response.validation.model_dump_json()
            )
            raise HTTPException(status_code=422, detail=response.validation)

        # Add new mappings
        response = await self.add_features_and_agents(
            arena_id, updateRequest, features, agents, clean=True, log=log
        )
        if not response.success:
            log.info(
                "Failed to map features and agents: %s",
                response.validation.model_dump_json(),
            )
            raise HTTPException(status_code=422, detail=response.validation)

        log.info("Updated arena: %s", arena_id)
        return self.arena_factory.build(arenaDTO)

    async def add_features_and_agents(
        self,
        arena_id: str,
        createRequest: ArenaCreateRequest,
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
            module="arena_controller",
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
                FeatureDTO(
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
                boundlog.error(
                    "Failed to map features to arena %s, rolling-back", arena_id
                )
                # db.execute("ROLLBACK")
                return problems[0]

        locallog.debug("Mapped %i features to arena %s", len(features), arena_id)

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
                        "Failed to map agent %s to arena %s, rolling-back",
                        agentReq.id,
                        arena_id,
                    )
                    # db.execute("ROLLBACK")
                    return ModelResponse(success=False, validation=response.validation)
        locallog.debug("Mapped %i agents to arena %s", len(agents), arena_id)

        # db.execute("COMMIT")
        return ModelResponse(success=True)

    def get_router(self):
        router = APIRouter(prefix="/arena", tags=["arena"])

        @router.post("/", response_model=Arena)
        async def create(req: ArenaCreateRequest):
            return await self.create_arena(req)

        @router.get("/{obj_id}", response_model=Arena)
        async def get(obj_id: str):
            return await self.get_arena(obj_id)

        @router.get("/", response_model=List[ArenaDTO])
        async def list_all():
            return await self.get_model_list()

        @router.get("/list", response_model=List[ArenaDTO])
        async def list_alias():
            return await self.get_model_list()

        @router.put("/", response_model=ArenaCreateRequest)
        async def update(req_id: str, req: ArenaCreateRequest):
            return await self.update_arena(req_id, req)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            return await self.delete_model(obj_id)

        return router


def get_invalid_features(
    features: List[FeatureDTO],
) -> List[Tuple[FeatureDTO, ModelResponse]]:
    """
    Validate the features.
    Args:
        features: The list of features to get

    Returns:
        A list of invalid validations
    """
    if features is None:
        return []

    return DbBase.validate_list(features)
