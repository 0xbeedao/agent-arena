"""
Judge models for the Agent Arena application.
"""

from typing import List
from typing import Optional
from typing import Tuple

from pydantic import Field

from .dbbase import DbBase


class JudgeResultDTO(DbBase, table=True):
    """
    Represents the result of a judge's evaluation.

    Maps to the JUDGE_RESULT entity in the ER diagram.
    """

    contest_id: str = Field(description="Contest identifier")
    result: str = Field(description="Result description")
    reason: Optional[str] = Field(default=None, description="Reason for the result")

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("contest_id", "contests", "id")]
