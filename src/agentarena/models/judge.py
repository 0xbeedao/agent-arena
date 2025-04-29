"""
Judge models for the Agent Arena application.
"""

from typing import Optional
from pydantic import BaseModel, Field

class JudgeResult(BaseModel):
    """
    Represents the result of a judge's evaluation.
    
    Maps to the JUDGE_RESULT entity in the ER diagram.
    """
    contest_id: str = Field(description="Contest identifier")
    result: str = Field(description="Result description")
    reason: Optional[str] = Field(default=None, description="Reason for the result")
    