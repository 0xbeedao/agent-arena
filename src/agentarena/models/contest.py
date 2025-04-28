"""
Contest model for the Agent Arena application.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from .dbmodel import DbBase

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
