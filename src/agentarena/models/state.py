"""
Arena state model for the Agent Arena application.
"""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from ulid import ULID

from .feature import Feature
from .player import PlayerState, PlayerAction
from .judge import JudgeResult


class ArenaState(BaseModel):
    """
    Represents the state of the arena at a specific point in time.
    
    Maps to the ARENA_STATE entity in the ER diagram.
    """
    id: ULID = Field(description="Unique identifier (ULID)")
    contest_id: str = Field(description="Reference to Contest")
    round_no: int = Field(description="Round number", ge=0)
    schema_version: int = Field(description="Schema version")
    narrative: Optional[str] = Field(default=None, description="Round narrative")
    state: str = Field(description="Arena state")
    timestamp: datetime = Field(description="Timestamp")
    
    # These fields are from the OpenAPI schema but not in the ER diagram
    features: List[Feature] = Field(default_factory=list, description="Arena features")
    player_states: Dict[str, PlayerState] = Field(default_factory=dict, description="Player states")
    player_actions: Dict[str, PlayerAction] = Field(default_factory=dict, description="Player actions")
    judge_results: Dict[str, JudgeResult] = Field(default_factory=dict, description="Judge results")