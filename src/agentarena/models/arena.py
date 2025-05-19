"""
Arena configuration model for the Agent Arena application.
"""

from typing import Dict
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from .dbbase import DbBase
from .feature import Feature
from .feature import FeatureRequest
from .participant import Participant
from .participant import ParticipantRequest
from .participant import ParticipantRole


class ArenaDTO(DbBase, table=True):
    """
    Configuration for an arena.

    Maps to the ARENA_CONFIG entity in the ER diagram.
    """

    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    winning_condition: str = Field(description="winning condition description")
    max_random_features: int = Field(
        description="Maximum number of random features", ge=0
    )


class ArenaCreateRequest(BaseModel):
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    winning_condition: str = Field(description="winning condition description")
    max_random_features: int = Field(
        description="Maximum number of random features", ge=0
    )
    features: Optional[List[FeatureRequest]] = Field(
        default=None, description="Features associated with the arena"
    )
    agents: Optional[List[ParticipantRequest]] = Field(
        default=None, description="Agents associated with the arena"
    )


class Arena(BaseModel):
    """
    Represents an arena configuration.

    This is a convenience class, and is not saved to DB as such, but used by the [arena_controller] to
    create the various parts of the arena setup
    """

    id: str = Field(description="Arena ID")
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    max_random_features: int = Field(
        description="Maximum number of random features", ge=0
    )
    features: List[Feature] = Field(
        default=None, description="Features associated with the arena"
    )
    participants: List[Participant] = Field(
        default=None, description="Participants associated with the arena"
    )

    def participants_by_role(self) -> Dict[ParticipantRole, Participant]:
        """
        Returns a list of agents by their role.
        """
        # collect the agents by role
        parts_by_role = {
            ParticipantRole.ANNOUNCER: [],
            ParticipantRole.ARENA: [],
            ParticipantRole.JUDGE: [],
            ParticipantRole.PLAYER: [],
        }
        for participant in self.participants:
            if participant.role not in parts_by_role:
                raise f"Unknown role: {participant.role}"
            parts_by_role[participant.role].append(participant)
        return parts_by_role
