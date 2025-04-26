"""
Strategy model for the Agent Arena application.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from ulid import ULID

class Strategy(BaseModel):
    """
    Represents a strategy that can be used by an agent.
    
    Maps to the STRATEGY entity in the ER diagram.
    """
    id: ULID = Field(description="Unique identifier (ULID)")
    name: str = Field(description="Strategy name")
    personality: str = Field(description="Personality description")
    instructions: str = Field(description="Strategy instructions")
    created_at: datetime = Field(description="Creation timestamp")