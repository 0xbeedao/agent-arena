"""
Agent controller for the Agent Arena application.
Handles HTTP requests for agent operations.
"""

from typing import Dict
from typing import List

import structlog
from dependency_injector.wiring import Provide
from dependency_injector.wiring import inject
from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException

from agentarena.containers.container import Container
from agentarena.models.agent import AgentDTO
from agentarena.services.model_service import ModelService

# Create a router for agent endpoints
router = APIRouter(tags=["Agent"])
log = structlog.get_logger("agent_controller").bind(module="agent_controller")


@router.post("/agent", response_model=Dict[str, str])
@inject
async def create_agent(
    agent_config: AgentDTO,
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
) -> Dict[str, str]:
    """
    Create a new agent.

    Args:
        agent_config: The agent configuration
        agent_service: The agent service

    Returns:
        A dictionary with the ID of the created agent
    """
    [id, response] = await agent_service.create(agent_config)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"id": id}


@router.get("/agent/{agent_id}", response_model=AgentDTO)
@inject
async def get_agent(
    agent_id: str,
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
) -> AgentDTO:
    """
    Get an agent by ID.

    Args:
        agent_id: The ID of the agent to get
        agent_service: The agent service

    Returns:
        The agent configuration

    Raises:
        HTTPException: If the agent is not found
    """
    [agent, response] = await agent_service.get(agent_id)
    if not response.success:
        raise HTTPException(status_code=404, detail=response.error)
    return agent


@router.get("/agent", response_model=List[AgentDTO])
@inject
async def get_agent_list(
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
) -> List[AgentDTO]:
    """
    Get a list of all agents.

    Args:
        agent_service: The agent service

    Returns:
        A list of agent configurations
    """
    return await agent_service.list()


@router.put("/agent/{agent_id}", response_model=Dict[str, bool])
@inject
async def update_agent(
    agent_id: str,
    agent_config: AgentDTO,
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
) -> Dict[str, bool]:
    """
    Update an agent.

    Args:
        agent_id: The ID of the agent to update
        agent_config: The new agent configuration
        agent_service: The agent service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the agent is not found
    """
    response = await agent_service.update(agent_id, agent_config)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}


@router.delete("/agent/{agent_id}", response_model=Dict[str, bool])
@inject
async def delete_agent(
    agent_id: str,
    agent_service: ModelService[AgentDTO] = Depends(Provide[Container.agent_service]),
) -> Dict[str, bool]:
    """
    Delete an agent.

    Args:
        agent_id: The ID of the agent to update
        agent_config: The new agent configuration
        agent_service: The agent service

    Returns:
        A dictionary indicating success

    Raises:
        HTTPException: If the agent is not found
    """
    response = await agent_service.delete_model(agent_id, agent_service)
    if not response.success:
        raise HTTPException(status_code=422, detail=response.validation)
    return {"success": response.success}
