"""
Agent service for the Agent Arena application.
Handles business logic for agent operations.
"""

from typing import Optional, Dict, List
from ulid import ULID
from agentarena.models.agent import AgentConfig
from .db_service import DbService

import json
import structlog
class AgentService:
    """Service for agent operations."""
    
    def __init__(self, dbService: DbService):
        """Initialize the agent service."""
        self.table = dbService.db['agents']
        self.dbService = dbService
        self.log = structlog.get_logger('agentservice').bind(module="agentservice")
    
    async def create_agent(self, agent_config: AgentConfig) -> str:
        """
        Create a new agent.
        
        Args:
            agent_config: The agent configuration
            
        Returns:
            The ID of the created agent
        """
        db_agent = agent_config.model_copy()
        if db_agent.id is None:
            db_agent.id = ULID().hex

        agent_id = str(db_agent.id)
 
        self.table.insert(db_agent.model_dump(), pk="id")
        self.log.info("Added agent: %s", agent_id)
        self.dbService.add_audit_log("Added agent: %s" % agent_id)
        return agent_id
    
    async def get_agent(self, agent_id: str) -> Optional[AgentConfig]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: The ID of the agent to get
            
        Returns:
            The agent configuration, or None if not found
        """
        # In a real implementation, this would query a database
        row = self.table.get(agent_id)
        self.log.info("Getting agent: %s", agent_id)
        return AgentConfig.model_validate(row) if row is not None else None
            
    async def update_agent(self, agent_id: str, agent_config: AgentConfig) -> bool:
        """
        Update an agent.
        
        Args:
            agent_id: The ID of the agent to update
            agent_config: The new agent configuration
            
        Returns:
            True if the agent was updated, False if not found
        """
        # In a real implementation, this would update a database record
        agent = await self.get_agent(agent_id)
        if agent is None:
            self.log.warn("No such agent to update: %s", agent_id)
            return False
        updated = agent_config.model_dump(exclude=["id"])
        self.table.update(agent_id, updated)
        self.dbService.add_audit_log("Updated agent %s: %s" % (agent_id, json.dumps(updated)))
        return True
    
    async def delete_agent(self, agent_id: str) -> bool:
        """
        Delete an agent.
        
        Args:
            agent_id: The ID of the agent to delete
            
        Returns:
            True if the agent was deleted, False if not found
        """
        # Check if the agent exists before deleting
        agent = await self.get_agent(agent_id)
        if agent is None:
            self.log.warn("No such agent to delete: %s", agent_id)
            return False
            
        self.table.delete(agent_id)
        self.log.info("Deleted agent: %s", agent_id)
        self.dbService.add_audit_log("Deleted agent: %s" % agent_id)
        return True
    
    async def list_agents(self) -> List[AgentConfig]:
        """
        List all agents.
        
        Returns:
            A list of all agent configurations
        """
        return [AgentConfig.model_validate(row) for row in self.table.rows]
    