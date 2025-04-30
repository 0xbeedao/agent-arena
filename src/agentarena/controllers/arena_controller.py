"""
Arena controller for the Agent Arena application.
Handles HTTP requests for arena operations.
"""

from sqlite_utils import Database
from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, List, Tuple

from agentarena.models.arena import ArenaConfig, ArenaCreateRequest, ArenaFeature, ArenaAgent
from agentarena.models.feature import Feature
from agentarena.models.agent import AgentConfig
from agentarena.models.validation import ValidationResponse
from agentarena.services.model_service import ModelResponse, ModelService
from agentarena.config.containers import Container

import structlog

# Create a router for arena endpoints
router = APIRouter(tags=["Arena"])
log = structlog.get_logger("arena_controller").bind(module="arena_controller")

@router.post("/arena", response_model=Dict[str, str])
@inject
async def create_arena(
    createRequest: ArenaCreateRequest,
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service]),
    feature_service: ModelService[Feature] = Depends(Provide[Container.feature_service]),
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service]),
    arenafeature_service: ModelService[ArenaFeature] = Depends(Provide[Container.arenafeature_service]),
    arenaagent_service: ModelService[ArenaAgent] = Depends(Provide[Container.arenaagent_service])
) -> Dict[str, str]:
    """
    Create a new arena.

    Args:
        arena_config: The arena configuration
        arena_service: The arena service

    Returns:
        A dictionary with the ID of the created arena
    """
    arena_config = ArenaConfig(
        name=createRequest.name,
        description=createRequest.description,
        height=createRequest.height,
        width=createRequest.width,
        rules=createRequest.rules,
        max_random_features=createRequest.max_random_features)
    
    features = []
    agents = []

    # get and validate the features
    features, feature_response = await get_features(createRequest.features, feature_service)
    if not feature_response.success:
        log.info("Invalid features: %s", feature_response.model_dump_json())
        raise HTTPException(status_code=422, detail=feature_response.model_dump_json())

    # repeat for agents
    agents, agent_response = await get_agents(createRequest.agents, agent_service)
    if not agent_response.success:
        log.info("Invalid agents: %s", agent_response.model_dump_json())
        raise HTTPException(status_code=422, detail=agent_response.model_dump_json)
     
    # create the new arena
    [arena_id, response] = await arena_service.create(arena_config)
    if not response.success:
        log.info("Failed to create arena: %s", response.validation.model_dump_json())
        raise HTTPException(status_code=422, detail=response.validation.model_dump_json)
    
    # Map the features to the arena
    if (len(features) + len(agents)) > 0:
        response = await add_features_and_agents(createRequest, features, agents, arenafeature_service, arenaagent_service)
        if not response.success:
            log.info("Failed to map features and agents: %s", response.validation.model_dump_json())
            raise HTTPException(status_code=422, detail=response.validation.model_dump_json())
        
    # If we get here, the arena was created successfully
    return {"id": arena_id}

@router.get("/arena/{arena_id}", response_model=ArenaConfig)
@inject
async def get_arena(
    arena_id: str,
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
) -> ArenaConfig:
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
    [arena, response] = await arena_service.get(arena_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return arena

@router.get("/arena", response_model=List[ArenaConfig])
@inject
async def get_arena_list(
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
) -> List[ArenaConfig]:
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
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service]),
    feature_service: ModelService[Feature] = Depends(Provide[Container.feature_service]),
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service]),
    arenaagent_service: ModelService[ArenaAgent] = Depends(Provide[Container.arenaagent_service]),
    arenafeature_service: ModelService[ArenaFeature] = Depends(Provide[Container.arenafeature_service]),
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
    # get and validate the features
    features, invalid_features = await get_features(updateRequest.features, feature_service)
    if invalid_features:
        log.info("Invalid features: %s", invalid_features.validation.model_dump_json())
        raise HTTPException(status_code=422, detail=invalid_features.validation)

    # repeat for agents
    agents, invalid_agents = await get_agents(updateRequest.agents, agent_service)
    if invalid_agents:
        log.info("Invalid agents: %s", invalid_agents.validation.model_dump_json())
        raise HTTPException(status_code=422, detail=invalid_agents.validation)
    
    arena_config = ArenaConfig(
        name=updateRequest.name,
        description=updateRequest.description,
        height=updateRequest.height,
        width=updateRequest.width,
        rules=updateRequest.rules,
        max_random_features=updateRequest.max_random_features
    )
    response = await arena_service.update(arena_id, arena_config)
    if not response.success:
        log.info("Failed to update arena: %s", response.validation.model_dump_json())
        raise HTTPException(status_code=422, detail=response.validation)
    
    # delete old mappings
    db.begin_transaction()
    db = arena_service.table.execute("DELETE FROM arena_features WHERE arena_config_id = ?", [arena_id])
    db = arenaagent_service.table.execute("DELETE FROM arena_agents WHERE arena_config_id = ?", [arena_id])
    
    # Add new mappings
    response = await add_features_and_agents(arena_id, updateRequest, features, agents, arenafeature_service, arenaagent_service)
    if not response.success:
        db.rollback()
        log.info("Failed to map features and agents: %s", response.validation.model_dump_json())
        raise HTTPException(status_code=422, detail=response.validation)
    db.commit_transaction()

    return {"success": response.success}

@router.delete("/arena/{arena_id}", response_model=Dict[str, bool])
@inject
async def delete_arena(
    arena_id: str,
    arena_service: ModelService[ArenaConfig] = Depends(Provide[Container.arena_service])
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

async def add_features_and_agents(
    arena_id: str,
    createRequest: ArenaCreateRequest,
    features: List[Feature],
    agents: List[AgentConfig],
    arenafeature_service: ModelService[ArenaFeature],
    arenaagent_service: ModelService[ArenaAgent],
) -> ModelResponse:
    """
    Add features and agents to the arena.

    Args:
        createRequest: The arena creation request
        features: The list of features to add
        agents: The list of agents to add
    """
    db = arenafeature_service.dbService.db
    db .begin_transaction()
    boundlog = log.bind(transaction=True, featureCt=len(features), agentCt=len(agents))
    boundlog.info("Mapping features and agents to arena")
    if len(features) > 0:
        featureMap = {feature.id: feature for feature in features}
        for featureReq in createRequest.features:
            feature = featureMap[featureReq.feature_id]

            arena_feature = ArenaFeature(
                arena_config_id=arena_id,
                feature_id=feature.id,
                position=featureReq.position,
                end_position=featureReq.end_position
            )
            [_, response] = await arenafeature_service.create(arena_feature)
            if not response.success:
                boundlog.error("Failed to map feature %s to arena %s, rolling-back", feature.id, arena_id)
                db.rollback()
                return ModelResponse(success=False, validation=response.validation)

    # Map the agents to the arena
    if (len(agents) > 0):
        agentMap = {agent.id: agent for agent in agents}
        for agentReq in createRequest.agents:
            agent = agentMap[agentReq.agent_id]
            arena_agent = ArenaAgent(
                arena_config_id=arena_id,
                agent_id=agent.id,
                role=agentReq.role,
            )
            [_, response] = await arenaagent_service.create(arena_agent)
            if not response.success:
                boundlog.error("Failed to map agent %s to arena %s, rolling-back", agent.id, arena_id)
                db.rollback()
                return ModelResponse(success=False, validation=response.validation)

    db.commit_transaction()
    return ModelResponse(success=True)

async def get_features(
    features: List[ArenaFeature],
    feature_service: ModelService[Feature]
) -> Tuple[List[ArenaFeature], ModelResponse]:
    """
    Get the features by ID.

    Args:
        features: The list of features to get
        arenafeature_service: The arena feature service

    Returns:
        A list of features
    """
    if features is None:
        return [], ModelResponse(success=True)
    
    # get the features by ID
    feature_ids = [feature.feature_id for feature in features]

    responses = await feature_service.get_by_ids(feature_ids)
    features, validations = zip(*responses)
    invalids = [feature_id for [feature_id, response] in validations if not response.success]
    if invalids:
        return features, ModelResponse(success=False, validation=ValidationResponse(valid=False, message="Invalid feature IDs: " + ", ".join(invalids)))
    return features, ModelResponse(success=True)
    
async def get_agents(
    agents: List[ArenaAgent],
    agent_service: ModelService[AgentConfig]
) -> Tuple[List[ArenaAgent], ModelResponse]:
    """
    Get the agents by ID.

    Args:
        agents: The list of agents to get
        arenaagent_service: The arena agent service

    Returns:
        A list of agents
    """
    if agents is None:
        return [], ModelResponse(success=True)
    
    # get the agents by ID
    agent_ids = [agent.agent_id for agent in agents]

    responses = await agent_service.get_by_ids(agent_ids)
    agents, validations = zip(*responses)
    invalids = [agent_id for [agent_id, response] in validations if not response.success]
    if invalids:
        return agents, ModelResponse(success=False, validation=ValidationResponse(valid=False, message="Invalid agent IDs: " + ", ".join(invalids)))
    
    return agents, ModelResponse(success=True)