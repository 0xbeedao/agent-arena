"""
Strategy model for the Agent Arena application.
"""

from typing import Optional
from pydantic import Field
from .dbmodel import DbBase
class Strategy(DbBase):
    """
    Represents a strategy that can be used by an agent.
    
    Maps to the STRATEGY entity in the ER diagram.
    """
    name: Optional[str] = Field(default="", description="Strategy name")
    personality: Optional[str] = Field(default="", description="Personality description")
    instructions: Optional[str] = Field(default="", description="Strategy instructions")
