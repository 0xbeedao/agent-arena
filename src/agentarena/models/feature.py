"""
Feature model for the Agent Arena application.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from .dbmodel import DbBase


class FeatureDTO(DbBase):
    """
    Represents a feature in the arena DB.

    Maps to the FEATURE entity in the ER diagram.
    """

    arena_config_id: str = Field(description="Reference to ArenaDTO")
    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    position: str = Field(
        description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$"
    )
    origin: str = Field(description="Feature type")
    end_position: Optional[str] = Field(
        default=None,
        description="End coordinate for features with area",
        pattern=r"^-?\d+,-?\d+$",
    )

    def get_foreign_keys(self) -> list[tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("arena_config_id", "arenas", "id")]


class FeatureOriginType(Enum):
    """
    Enum for feature types.
    """

    REQUIRED = "required"
    RANDOM = "random"


class FeatureRequest(DbBase):
    """
    Request model for creating a feature
    """

    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    position: str = Field(
        description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$"
    )
    end_position: Optional[str] = Field(
        default=None,
        description="End coordinate for features with area",
        pattern=r"^-?\d+,-?\d+$",
    )


class Feature(BaseModel):
    """
    Feature model for the Agent Arena application.

    Maps to the FEATURE entity in the ER diagram.
    """

    id: str = Field(description="Feature identifier")
    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    position: str = Field(
        description="Grid coordinate as 'x,y'", pattern=r"^-?\d+,-?\d+$"
    )
    origin: FeatureOriginType = Field(description="Feature Origin (required/random)")
    end_position: Optional[str] = Field(
        default=None,
        description="End coordinate for features with area",
        pattern=r"^-?\d+,-?\d+$",
    )

    @staticmethod
    def from_dto(dto: FeatureDTO):
        """
        Converts a FeatureDTO to a Feature.
        """
        return Feature(
            id=dto.id,
            name=dto.name,
            description=dto.description,
            position=dto.position,
            end_position=dto.end_position,
            origin=FeatureOriginType(dto.origin),
        )
