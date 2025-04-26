"""
Contest model for the Agent Arena application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from ulid import ULID

class ContestStatus(str, Enum):
    """
    Status of a contest.
    """
    CREATED = "created"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Contest(BaseModel):
    """
    Represents a contest between agents.
    
    Maps to the CONTEST entity in the ER diagram.
    """
    id: ULID = Field(description="Unique identifier (ULID)")
    arena_config_id: str = Field(description="Reference to ArenaConfig")
    status: ContestStatus = Field(description="Contest status")
    started_at: Optional[datetime] = Field(default=None, description="Start timestamp")
    ended_at: Optional[datetime] = Field(default=None, description="End timestamp")