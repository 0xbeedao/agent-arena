"""
Feature model for the Agent Arena application.
"""

from typing import Optional
from pydantic import BaseModel, Field
from ulid import ULID

class Feature(BaseModel):
    """
    Represents a feature in the arena.
    
    Maps to the FEATURE entity in the ER diagram.
    """
    id: ULID = Field(description="Unique identifier (ULID)")
    name: str = Field(description="Feature name")
    position: str = Field(description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$")
    end_position: Optional[str] = Field(
        default=None, 
        description="End coordinate for features with area",
        pattern=r"^-?\d+,-?\d+$"
    )
    state: Optional[str] = Field(default=None, description="Feature state")