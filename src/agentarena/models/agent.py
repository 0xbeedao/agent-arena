"""
Agent configuration model for the Agent Arena application.
"""

from typing import Optional
from pydantic import BaseModel, Field
from ulid import ULID

class AgentConfig(BaseModel):
    """
    Configuration for an agent.
    
    Maps to the AGENT_CONFIG entity in the ER diagram.
    """
    id: ULID = Field(description="Unique identifier (ULID)")
    name: str = Field(description="Agent name")
    endpoint: str = Field(description="API endpoint for the agent")
    api_key: str = Field(description="API key for authentication")
    metadata: str = Field(description="Additional metadata")
    strategy_id: str = Field(description="Reference to Strategy")