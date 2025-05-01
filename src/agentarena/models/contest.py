"""
Contest model for the Agent Arena application.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from .dbmodel import DbBase

class ContestRole(str, Enum):
    """
    Roles for agents in contests
    """
    PLAYER = "player"
    ARENA = "arena"
    JUDGE = "judge"
    ANNOUNCER = "announcer"
class ContestStatus(str, Enum):
    """
    Status of a contest.
    """
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
class Contest(DbBase):
    """
    Represents a contest between agents.
    
    Maps to the CONTEST entity in the ER diagram.
    """
    arena_config_id: str = Field(description="Reference to ArenaConfig")
    status: ContestStatus = Field(default=ContestStatus.CREATED, description="Contest status")
    start_time: Optional[datetime] = Field(default=None, description="Contest start time")
    end_time: Optional[datetime] = Field(default=None, description="Contest end time")

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [
            ("arena_id", "arenas", "id")
        ]
class ContestAgent(DbBase):
    """
    Maps agents to contests
    """

    role: str = Field(description="Role in contest")
    contest_id: str = Field(description="Reference to a Contest")
    agent_id: str = Field(description="Reference to the Agent playing this role")

    # Not a Pydantic Field, this is used by the DB to set up FKs
    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [
            ("contest_id", "contests", "id"),
            ("agent_id", "agents", "id")
        ]

class ContestAgentRequest(BaseModel):
    """
    Request model for creating a contest agent
    """
    role: ContestRole = Field(description="Role in contest")
    agent_id: str = Field(description="Reference to the Agent playing this role")