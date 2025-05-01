"""
Arena configuration model for the Agent Arena application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from pydantic import BaseModel, Field

from agentarena.models.feature import Feature, FeatureRequest
from .dbmodel import DbBase


class AgentRole(str, Enum):
    """
    Enum for different roles
    """
    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"
    ANNOUNCER = "announcer"


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
    
class ArenaAgent(DbBase):
    """
    Maps agents to arenas
    """
    arena_config_id: str = Field(description="Reference to ArenaConfig")
    agent_id: str = Field(description="Reference to Agent")
    role: str = Field(description="Role in arena") # note, str - enum is not supported in sqlite3

    def get_foreign_keys(self) -> list[tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [
            ("arena_config_id", "arenas", "id"),
            ("agent_id", "agents", "id")
        ]
    
class ArenaAgentRequest(BaseModel):
    """
    Request model for creating an arena agent
    """
    agent_id: str = Field(description="Reference to Agent")
    role: AgentRole = Field(description="Role in arena")

class ArenaCreateRequest(BaseModel):
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(description="Maximum number of random features", ge=0)
    features: Optional[List[FeatureRequest]] = Field(
        default=None, 
        description="Features associated with the arena"
    )
    agents: Optional[List[ArenaAgentRequest]] = Field(
        default=None, 
        description="Agents associated with the arena"
    )

class Arena(BaseModel):
    """
    Represents an arena configuration.
    
    This is a convenience class, and is not saved to DB as such, but used by the [arena_controller] to
    create the various parts of the arena setup
    """
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(description="Maximum number of random features", ge=0)
    features: Optional[Feature] = Field(
        default=None, 
        description="Features associated with the arena"
    )
    agents: Optional[ArenaAgent] = Field(
        default=None, 
        description="Agents associated with the arena"
    )
