"""
Round statistics model for the Agent Arena application.
"""

from typing import Any
from typing import Dict
from typing import List
from typing import Tuple

from pydantic import Field

from .dbbase import DbBase


class RoundStatsDTO(DbBase, table=True):
    """
    Statistics for a round.

    Maps to the ROUND_STATS entity in the ER diagram.
    """

    arenastate_id: str = Field(description="Reference to ArenaState")
    actions_count: int = Field(description="Number of actions in the round")
    duration_ms: int = Field(description="Round duration in milliseconds")
    metrics_json: Dict[str, Any] = Field(description="Additional metrics as JSON")

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("arenastate_id", "arenastates", "id")]
