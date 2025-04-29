"""
Round statistics model for the Agent Arena application.
"""

from typing import Dict, Any
from pydantic import BaseModel, Field
from .dbmodel import DbBase

class RoundStats(DbBase):
    """
    Statistics for a round.
    
    Maps to the ROUND_STATS entity in the ER diagram.
    """
    arena_state_id: str = Field(description="Reference to ArenaState")
    actions_count: int = Field(description="Number of actions in the round")
    duration_ms: int = Field(description="Round duration in milliseconds")
    metrics_json: Dict[str, Any] = Field(description="Additional metrics as JSON")
