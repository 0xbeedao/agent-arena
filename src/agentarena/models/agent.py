"""
Agent configuration model for the Agent Arena application.
"""

from typing import Optional
from pydantic import Field
from .dbmodel import DbBase

class AgentConfig(DbBase):
    """
    Configuration for an agent.
    
    Maps to the AGENT_CONFIG entity in the ER diagram.
    """
    name: Optional[str] = Field(default="", description="Agent name")
    endpoint: Optional[str] = Field(default="", description="API endpoint for the agent")
    api_key: Optional[str] = Field(default="", description="API key for authentication")
    metadata: Optional[str] = Field(default="", description="Additional metadata")
    strategy_id: Optional[str] = Field(default="", description="Reference to Strategy")
