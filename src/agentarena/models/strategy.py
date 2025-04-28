"""
Strategy model for the Agent Arena application.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field

class Strategy(BaseModel):
    """
    Represents a strategy that can be used by an agent.
    
    Maps to the STRATEGY entity in the ER diagram.
    """
    id: Optional[str] = Field(default=None, description="Unique identifier (ULID)")
    name: Optional[str] = Field(default="", description="Strategy name")
    personality: Optional[str] = Field(default="", description="Personality description")
    instructions: Optional[str] = Field(default="", description="Strategy instructions")
    created_at: Optional[datetime] = Field(default=None, description="Creation timestamp")