"""
Arena configuration model for the Agent Arena application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from .dbmodel import DbBase


class AgentRole(str, Enum):
    """
    Enum for different roles
    """
    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"
class ArenaConfig(DbBase):
    """
    Configuration for an arena.
    
    Maps to the ARENA_CONFIG entity in the ER diagram.
    """
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(description="Maximum number of random features", ge=0)

class ArenaFeatures(DbBase):
    """
    Maps features to arenas
    """
    arena_config_id: str = Field(description="Reference to ArenaConfig")
    feature_id: str = Field(description="Reference to Feature")
    position: str = Field(description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$")
    end_position: str = Optional[Field(
        default=None, 
        description="End coordinate for features with area",
        pattern=r"^-?\d+,-?\d+$"
    )]

    def get_foreign_keys(self) -> list[tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [
            ("arena_config_id", "arenas", "id"),
            ("feature_id", "features", "id")
        ]
    
class ArenaAgents(DbBase):
    """
    Maps agents to arenas
    """
    arena_config_id: str = Field(description="Reference to ArenaConfig")
    agent_id: str = Field(description="Reference to Agent")
    role: AgentRole = Field(description="Role in arena")

    def get_foreign_keys(self) -> list[tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [
            ("arena_config_id", "arenas", "id"),
            ("agent_id", "agents", "id")
        ]
    
class Arena(BaseModel):
    """
    Represents an arena configuration.
    
    This is a convenience class, and is not saved to DB as such, but used by the [arena_controller] to
    create the various parts of the arena setup
    """
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(description="Maximum number of random features", ge=0)
    features: Optional[ArenaFeatures] = Field(
        default=None, 
        description="Features associated with the arena"
    )
    agents: Optional[ArenaAgents] = Field(
        default=None, 
        description="Agents associated with the arena"
    )
