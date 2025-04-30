"""
Arena configuration model for the Agent Arena application.
"""

from datetime import datetime
from pydantic import Field
from .dbmodel import DbBase
class ArenaConfig(DbBase):
    """
    Configuration for an arena.
    
    Maps to the ARENA_CONFIG entity in the ER diagram.
    """
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(description="Maximum number of random features", ge=0)
