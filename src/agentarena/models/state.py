"""
Arena state model for the Agent Arena application.
"""

from typing import Dict, List, Optional, Tuple

from pydantic import Field

from .dbmodel import DbBase
from .feature import FeatureDTO
from .judge import JudgeResultDTO
from .player import PlayerAction, PlayerStateDTO


class ArenaStateDTO(DbBase):
    """
    Represents the state of the arena at a specific point in time.

    Maps to the ARENA_STATE entity in the ER diagram.
    """

    contest_id: str = Field(description="Reference to Contest")
    round_no: int = Field(description="Round number", ge=0)
    narrative: Optional[str] = Field(default=None, description="Round narrative")
    state: str = Field(description="Arena state")
    features: List[FeatureDTO] = Field(
        default_factory=list, description="Arena features"
    )
    player_states: Dict[str, PlayerStateDTO] = Field(
        default_factory=dict, description="Player states"
    )
    player_actions: Dict[str, PlayerAction] = Field(
        default_factory=dict, description="Player actions"
    )
    judge_results: Dict[str, JudgeResultDTO] = Field(
        default_factory=dict, description="Judge results"
    )

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("contest_id", "contests", "id")]
