"""
Agent controller for the Agent Arena application.
Handles HTTP requests for agent operations.
"""

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, HTTPException, Depends
from typing import Annotated, Dict, List
from ulid import ULID

from agentarena.models.agent import AgentConfig
from agentarena.services.model_service import ModelService
from agentarena.config.containers import Container

from . import repository
import structlog

# Create a router for agent endpoints
router = APIRouter(tags=["Agent"])
log = structlog.get_logger("agent_controller").bind(module="agent_controller")

@router.post("/agent", response_model=Dict[str, str])
@inject
async def create_agent(
    agent_config: AgentConfig,
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service])
) -> Dict[str, str]:
    """
    Create a new agent.
    
    Args:
        agent_config: The agent configuration
        agent_service: The agent service
        
    Returns:
        A dictionary with the ID of the created agent
    """
    return await repository.create_model(agent_config, agent_service)

@router.get("/agent/{agent_id}", response_model=AgentConfig)
@inject
async def get_agent(
    agent_id: str,
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service])
) -> AgentConfig:
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
    return await repository.get_model(agent_id, agent_service)

@router.get("/agent", response_model=List[AgentConfig])
@inject
async def get_agent_list(
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service])
) -> List[AgentConfig]:
    """
    Get a list of all agents.
    
    Args:
        agent_service: The agent service
        
    Returns:
        A list of agent configurations
    """
    return await repository.get_model_list(agent_service)

@router.put("/agent/{agent_id}", response_model=Dict[str, bool])
@inject
async def update_agent(
    agent_id: str,
    agent_config: AgentConfig,
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service])
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
    return await repository.update_model(agent_id, agent_config, agent_service)

@router.put("/agent/{agent_id}", response_model=Dict[str, bool])
@inject
async def delete_agent(
    agent_id: str,
    agent_service: ModelService[AgentConfig] = Depends(Provide[Container.agent_service])
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
    return await repository.delete_model(agent_id, agent_service)

