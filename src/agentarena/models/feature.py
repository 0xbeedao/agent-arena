"""
Feature model for the Agent Arena application.
"""

from typing import Optional
from pydantic import Field
from .dbmodel import DbBase
class Feature(DbBase):
    """
    Represents a feature in the arena.
    
    Maps to the FEATURE entity in the ER diagram.
    """
    arena_config_id: str = Field(description="Reference to ArenaConfig")
    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    position: str = Field(description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$")
    end_position: Optional[str] = Field(
        default=None, 
        description="End coordinate for features with area",
        pattern=r"^-?\d+,-?\d+$"
    )

    def get_foreign_keys(self) -> list[tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [
            ("arena_config_id", "arenas", "id")
        ]


class FeatureRequest(DbBase):
    """
    Request model for creating a feature
    """
    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    position: str = Field(description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$")
    end_position: Optional[str] = Field(
        default=None, 
        description="End coordinate for features with area",
        pattern=r"^-?\d+,-?\d+$"
    )