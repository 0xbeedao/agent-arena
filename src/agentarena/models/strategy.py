"""
Strategy model for the Agent Arena application.
"""

from typing import Optional
from enum import Enum
from pydantic import Field
from .dbmodel import DbBase

class StrategyType(str, Enum):
    """
    Enum for different strategy types.
    """
    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"
    
class Strategy(DbBase):
    """
    Represents a strategy that can be used by an agent.
    
    Maps to the STRATEGY entity in the ER diagram.
    """
    name: Optional[str] = Field(default="", description="Strategy name")
    personality: Optional[str] = Field(default="", description="Personality description")
    instructions: Optional[str] = Field(default="", description="Strategy instructions")
    description: Optional[str] = Field(default="", description="Detailed description of the strategy")
    group: StrategyType = Field(default=StrategyType.PLAYER, description="Type of strategy")
