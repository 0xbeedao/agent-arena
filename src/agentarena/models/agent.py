"""
Agent configuration model for the Agent Arena application.
"""

from typing import Optional
from pydantic import BaseModel, Field

class AgentConfig(BaseModel):
    """
    Configuration for an agent.
    
    Maps to the AGENT_CONFIG entity in the ER diagram.
    """
    # AI note do not change this field to ULID type, we want to keep the native type for sqlite
    id: Optional[str] = Field(default=None, description="Unique identifier (ULID), auto-generated if not provided")
    name: Optional[str] = Field(default="", description="Agent name")
    endpoint: Optional[str] = Field(default="", description="API endpoint for the agent")
    api_key: Optional[str] = Field(default="", description="API key for authentication")
    metadata: Optional[str] = Field(default="", description="Additional metadata")
    strategy_id: Optional[str] = Field(default="", description="Reference to Strategy")
