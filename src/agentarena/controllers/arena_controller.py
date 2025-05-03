"""
Arena controller for the Agent Arena application.
Handles HTTP requests for arena operations.
"""

from typing import Dict, List, Tuple

import structlog
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from agentarena.config.containers import Container
from agentarena.models.agent import AgentDTO
from agentarena.models.arena import Arena, ArenaAgent, ArenaCreateRequest, ArenaDTO
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.dbmodel import DbBase
from agentarena.models.feature import FeatureDTO, FeatureOriginType
from agentarena.models.strategy import StrategyDTO
from agentarena.services.builder_service import make_arena
from agentarena.services.model_service import ModelResponse, ModelService

# Create a router for arena endpoints
router = APIRouter(tags=["Arena"])
log = structlog.get_logger("arena_controller").bind(module="arena_controller")


@router.post("/arena", response_model=Dict[str, str])
@inject
async def create_arena(
    createRequest: ArenaCreateRequest,
    arena_service: ModelService[ArenaDTO] = Depends(Provide[Container.arena_service]),
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
) -> Dict[str, str]:
    """
    Create a new arena.

    Args:
        arena_config: The arena configuration
        arena_service: The arena service

    Returns:
        A dictionary with the ID of the created arena
    """
    arena_config = ArenaDTO(
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
    _, problems = await agent_service.get_by_ids(agent_ids)
    if problems:
        for problem in problems:
            log.info("Invalid agent: %s", problem.model_dump_json())
        raise HTTPException(status_code=422, detail=problems[0].model_dump_json())

    # create the new arena
    [arena_id, response] = await arena_service.create(arena_config)
    if not response.success:
        log.info("Failed to create arena: %s", response.validation.model_dump_json())
        raise HTTPException(
            status_code=422, detail=response.validation.model_dump_json()
        )

    # Map the features to the arena
    if (len(features) + len(agents)) > 0:
        response = await add_features_and_agents(arena_id, createRequest)
        if not response.success:
            log.info(
                "Failed to map features and agents: %s",
                response.validation.model_dump_json(),
            )
            raise HTTPException(
                status_code=422, detail=response.validation.model_dump_json()
            )

    log.info("Created arena: %s", arena_id)
    # If we get here, the arena was created successfully
    return {"id": arena_id}


@router.get("/arena/{arena_id}", response_model=Arena)
@inject
async def get_arena(
    arena_id: str,
    arena_service: ModelService[ArenaDTO] = Depends(Provide[Container.arena_service]),
) -> Arena:
    """
    Get an arena by ID.

    Args:
        arena_id: The ID of the arena to get
        arena_service: The arena service

    Returns:
        The arena configuration

    Raises:
        HTTPException: If the arena is not found
    """
    [arena_config, response] = await arena_service.get(arena_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)

    return await make_arena(arena_config)


@router.get("/arena", response_model=List[ArenaDTO])
@inject
async def get_arena_list(
    arena_service: ModelService[ArenaDTO] = Depends(Provide[Container.arena_service]),
) -> List[ArenaDTO]:
    """
    Get a list of all arenas.

    Args:
        arena_service: The arena service

    Returns:
        A list of arena configurations
    """
    return await arena_service.list()


@router.put("/arena/{arena_id}", response_model=Dict[str, bool])
@inject
async def update_arena(
    arena_id: str,
    updateRequest: ArenaCreateRequest,
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
    arena_service: ModelService[ArenaDTO] = Depends(Provide[Container.arena_service]),
) -> Dict[str, bool]:
    """
    Update an arena.

    Args:
        arena_id: The ID of the arena to update
        arena_config: The new arena configuration
        arena_service: The arena service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the arena is not found
    """
    features = updateRequest.features
    agents = updateRequest.agents

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
    _, problems = await agent_service.get_by_ids(agent_ids)
    if problems:
        for problem in problems:
            log.info("Invalid agent: %s", problem.model_dump_json())
        raise HTTPException(status_code=422, detail=problems[0].model_dump_json())

    arena_config = ArenaDTO(
        name=updateRequest.name,
        description=updateRequest.description,
        height=updateRequest.height,
        width=updateRequest.width,
        rules=updateRequest.rules,
        max_random_features=updateRequest.max_random_features,
        winning_condition=updateRequest.winning_condition,
    )
    response = await arena_service.update(arena_id, arena_config)
    if not response.success:
        log.info("Failed to update arena: %s", response.validation.model_dump_json())
        raise HTTPException(status_code=422, detail=response.validation)

    # Add new mappings
    response = await add_features_and_agents(
        arena_id, updateRequest, features, agents, clean=True
    )
    if not response.success:
        log.info(
            "Failed to map features and agents: %s",
            response.validation.model_dump_json(),
        )
        raise HTTPException(status_code=422, detail=response.validation)

    log.info("Updated arena: %s", arena_id)
    return {"success": response.success}


@router.delete("/arena/{arena_id}", response_model=Dict[str, bool])
@inject
async def delete_arena(
    arena_id: str,
    arena_service: ModelService[ArenaDTO] = Depends(Provide[Container.arena_service]),
) -> Dict[str, bool]:
    """
    Delete an arena.

    Args:
        arena_id: The ID of the arena to delete
        arena_service: The arena service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the arena is not found
    """
    response = await arena_service.delete(arena_id)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}


@inject
async def add_features_and_agents(
    arena_id: str,
    createRequest: ArenaCreateRequest,
    clean: bool = False,
    feature_service: ModelService[FeatureDTO] = Depends(
        Provide[Container.feature_service]
    ),
    arenaagent_service: ModelService[ArenaAgentDTO] = Depends(
        Provide[Container.arenaagent_service]
    ),
) -> ModelResponse:
    """
    Add features and agents to the arena.

    Args:
        createRequest: The arena creation request
        features: The list of features to add
        agents: The list of agents to add
    """
    # If clean is true, delete the existing features and agents
    if clean:
        feature_service.table.delete_where("arena_config_id = :id", {"id": arena_id})
        arenaagent_service.table.delete_where("arena_config_id = :id", {"id": arena_id})

    features = createRequest.features
    agents = createRequest.agents
    # db.execute("BEGIN TRANSACTION")
    boundlog = log.bind(featureCt=len(features), agentCt=len(agents))
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

        _, problems = await feature_service.create_many(feature_objects)
        if problems:
            boundlog.error("Failed to map features to arena %s, rolling-back", arena_id)
            # db.execute("ROLLBACK")
            return problems[0]

    log.debug("Mapped %i features to arena %s", len(features), arena_id)

    # Map the agents to the arena
    if len(agents) > 0:
        for agentReq in agents:
            arena_agent = ArenaAgentDTO(
                arena_config_id=arena_id,
                agent_id=agentReq.agent_id,
                role=agentReq.role,
            )
            [_, response] = await arenaagent_service.create(arena_agent)
            if not response.success:
                boundlog.error(
                    "Failed to map agent %s to arena %s, rolling-back",
                    agent.id,
                    arena_id,
                )
                # db.execute("ROLLBACK")
                return ModelResponse(success=False, validation=response.validation)
    log.debug("Mapped %i agents to arena %s", len(agents), arena_id)

    # db.execute("COMMIT")
    return ModelResponse(success=True)


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
