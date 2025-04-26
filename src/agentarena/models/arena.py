"""
Arena configuration model for the Agent Arena application.
"""

from datetime import datetime
from pydantic import BaseModel, Field
from ulid import ULID

class ArenaConfig(BaseModel):
    """
    Configuration for an arena.
    
    Maps to the ARENA_CONFIG entity in the ER diagram.
    """
    id: ULID = Field(description="Unique identifier (ULID)")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(description="Maximum number of random features", ge=0)
    judge_id: str = Field(description="Reference to Judge agent")
    created_at: datetime = Field(description="Creation timestamp")