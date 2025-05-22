"""
Arena configuration model for the Agent Arena application.
"""

from enum import Enum
from typing import List
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

from ...models.dbbase import DbBase

# -------- Arena Models


class ArenaBase(SQLModel, table=False):
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    winning_condition: str = Field(description="winning condition description")
    max_random_features: int = Field(
        description="Maximum number of random features", ge=0
    )


class Arena(ArenaBase, DbBase, table=True):
    """
    Configuration for an arena.

    Maps to the ARENA_CONFIG entity in the ER diagram.
    """

    # Relationships
    features: List["Feature"] = Relationship(back_populates="arena")


class ArenaCreate(ArenaBase):
    features: List["FeatureCreate"] = Field(description="Required Features to Create")


class ArenaPublic(ArenaBase):
    id: str


class ArenaUpdate(SQLModel):
    name: Optional[str] = Field(default=None, description="Arena name")
    description: Optional[str] = Field(description="Arena description")
    height: Optional[int] = Field(description="Arena height", gt=0)
    width: Optional[int] = Field(description="Arena width", gt=0)
    rules: Optional[str] = Field(description="Game rules")
    winning_condition: Optional[str] = Field(
        description="winning condition description"
    )
    max_random_features: Optional[int] = Field(
        description="Maximum number of random features", ge=0
    )


# -------- Contest models


class ContestRole(str, Enum):
    """
    Roles for agents in contests
    """

    PLAYER = "player"
    ARENA = "arena"
    JUDGE = "judge"
    ANNOUNCER = "announcer"


class ContestState(str, Enum):
    """
    Status of a contest.
    """

    CREATED = "created"
    STARTING = "starting"
    STARTED = "started"
    PAUSED = "paused"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ContestBase(SQLModel, table=False):
    """
    Represents a specific run of a contest between agents.

    Maps to the CONTEST entity in the ER diagram.
    """

    arena_id: str = Field(description="Reference to ArenaDTO", foreign_key="arena.id")
    current_round: int = Field(default=1, description="Current round")
    player_positions: List[str] = Field(
        default=[], description="A list of player positions"
    )
    state: str = Field(default=ContestState.CREATED.value, description="Contest state")


class Contest(ContestBase, DbBase, table=True):
    winner_id: Optional[str] = Field(
        default=None,
        description="id of winning player agent",
        foreign_key="participant.id",
    )
    start_time: Optional[int] = Field(default=None, description="Contest start time")
    end_time: Optional[int] = Field(default=None, description="Contest end time")

    # relationships

    participants: List["Participant"] = Relationship(
        back_populates="contests", link_model="ContestParticipant"
    )


class ContestCreate(SQLModel, table=False):
    arena_id: str = Field(description="Arena ID", foreign_key="arena.id")
    player_positions: List[str] = Field(
        default=[], description="A list of player positions"
    )
    participant_ids: List[str] = Field(
        description="IDs of Participants", foreign_key="participant.id"
    )


class ContestPublic(ContestBase, table=False):
    id: str


class ContestUpdate(ContestBase):
    pass


# -------- Feature models


class FeatureOriginType(Enum):
    """
    Enum for feature types.
    """

    REQUIRED = "required"
    RANDOM = "random"


class FeatureBase(SQLModel, table=False):
    arena_id: str = Field(description="Reference to ArenaDTO", foreign_key="arena.id")
    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    position: str = Field(
        description="Grid coordinate as 'x,y'",
    )
    origin: str = Field(description="Feature type")
    end_position: Optional[str] = Field(
        default=None,
        description="End coordinate for features with area",
    )


class Feature(FeatureBase, DbBase, table=True):
    """
    Represents a feature in the arena DB.

    Maps to the FEATURE entity in the ER diagram.
    """

    arena: "Arena" = Relationship(back_populates="features")


class FeatureCreate(FeatureBase):
    """
    Request model for creating a feature
    """


class FeatureUpdate(SQLModel):
    arena_id: Optional[str] = Field(
        default=None, description="Reference to Arena", foreign_key="arena.id"
    )
    name: Optional[str] = Field(default=None, description="Feature name")
    description: Optional[str] = Field(default=None, description="Feature description")
    position: Optional[str] = Field(
        default=None,
        description="Grid coordinate as 'x,y'",
    )
    origin: Optional[str] = Field(default=None, description="Feature type")
    end_position: Optional[str] = Field(
        default=None,
        description="End coordinate for features with area",
    )


class FeaturePublic(FeatureBase):
    id: str


# -------- Participant Models


class ParticipantRole(Enum):
    """
    Enum for different roles
    """

    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"
    ANNOUNCER = "announcer"


class ParticipantBase(SQLModel, table=False):
    arena_id: str = Field(description="Reference to ArenaDTO", foreign_key="arena.id")
    name: str = Field(description="Participant name")
    role: str = Field(description="Role in arena")


class Participant(ParticipantBase, DbBase, table=True):
    """
    Maps agents to arenas
    """

    contests: List[Arena] = Relationship(
        back_populates="participants", link_model="ContestParticipant"
    )


class ParticipantCreate(ParticipantBase):
    """
    Request model for creating a participant
    """


class ParticipantPublic(ParticipantBase):
    """
    Public model for Participant
    """

    id: str


class ParticipantUpdate(SQLModel):
    """
    Request model for creating a participant
    """

    arena_id: Optional[str] = Field(
        default=None, description="Reference to ArenaDTO", foreign_key="arena.id"
    )
    name: Optional[str] = Field(default=None, description="Participant name")
    role: Optional[str] = Field(default=None, description="Role in arena")


class ContestParticipant(SQLModel, table=True):
    participant_id: Optional[str] = Field(
        default=None, foreign_key="participant.id", primary_key=True
    )
    contest_id: Optional[str] = Field(
        default=None, foreign_key="contest.id", primary_key=True
    )
