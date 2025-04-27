"""
Agent controller for the Agent Arena application.
Handles HTTP requests for agent operations.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from ulid import ULID

from agentarena.models.agent import AgentConfig
from agentarena.services.agent_service import AgentService

# Create a router for agent endpoints
router = APIRouter(tags=["Agent"])

# Dependency to get the agent service
def get_agent_service():
    """Dependency to get the agent service."""
    return AgentService()

@router.post("/agent", response_model=Dict[str, str])
async def create_agent(
    agent_config: AgentConfig,
    agent_service: AgentService = Depends(get_agent_service)
) -> Dict[str, str]:
    """
    Create a new agent.
    
    Args:
        agent_config: The agent configuration
        agent_service: The agent service
        
    Returns:
        A dictionary with the ID of the created agent
    """
    agent_id = await agent_service.create_agent(agent_config)
    return {"id": agent_id}

@router.get("/agent/{agent_id}", response_model=AgentConfig)
async def get_agent(
    agent_id: str,
    agent_service: AgentService = Depends(get_agent_service)
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
    agent = await agent_service.get_agent(agent_id)
    if agent is None:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    return agent

@router.put("/agent/{agent_id}", response_model=Dict[str, bool])
async def update_agent(
    agent_id: str,
    agent_config: AgentConfig,
    agent_service: AgentService = Depends(get_agent_service)
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
    success = await agent_service.update_agent(agent_id, agent_config)
    if not success:
        raise HTTPException(status_code=404, detail=f"Agent with ID {agent_id} not found")
    return {"success": True}