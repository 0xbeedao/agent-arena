"""
Public Pydantic models - suitable for passing between apps, with no SQLModel stuff to accidentally cause tables to be created.
"""

from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import ContestState
from agentarena.models.constants import RoleType


class ArenaPublic(BaseModel):
    id: str = Field(default="", description="ID")
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    max_random_features: int = Field(description="maximum random features", default=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    winning_condition: str = Field(description="winning condition description")


class ContestPublic(BaseModel):
    id: str = Field(default="", description="ID")
    arena: ArenaPublic = Field()
    end_time: int = Field(description="Timestamp")
    round: Optional["ContestRoundPublic"] = Field()
    start_time: int = Field(description="Timestamp")
    state: ContestState = Field(
        default=ContestState.CREATED, description="Contest state"
    )
    winner: Optional["ParticipantPublic"] = Field(default=None)


class ContestRoundPublic(BaseModel):
    features: List["FeaturePublic"] = Field(default=[], description="Feature list")
    narrative: str = Field(default="", description="Round narrative")
    players: List["PlayerPublic"] = Field(default=[])
    round_no: int = Field(description="Round number", ge=0)
    state: ContestRoundState = Field(description="Round state")


class FeaturePublic(BaseModel):
    description: str = Field(description="Feature description")
    name: str = Field(description="Feature name")
    position: str = Field(
        description="Grid coordinate as 'x,y'",
    )


class ParticipantPublic(BaseModel):
    id: str = Field(default="", description="ID")
    description: str = Field(
        default="",
        description="Agent description",
    )
    endpoint: str = Field(
        default="",
        description="API endpoint for the agent",
    )
    name: str = Field(
        description="Participant name",
        max_length=100,
        min_length=1,
    )
    role: RoleType = Field(
        description="Role in arena",
    )


class PlayerPublic(BaseModel):
    id: str = Field()
    name: str = Field()
    position: str = Field(description="x,y position")
    inventory: List[str] = Field(default=[], description="Player inventory")
    health: str = Field(default="Fresh", description="description of player health")
    score: int = Field(default=0, description="game score")
