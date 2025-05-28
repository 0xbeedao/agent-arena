"""
Arena configuration model for the Agent Arena application.
"""

from enum import Enum
from typing import Dict
from typing import List
from typing import Optional
from urllib.parse import urljoin

from sqlmodel import JSON
from sqlmodel import Column
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

from agentarena.models.dbbase import DbBase


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


class FeatureOriginType(str, Enum):
    """
    Enum for feature types.
    """

    REQUIRED = "required"
    RANDOM = "random"


class ParticipantRole(str, Enum):
    """
    Enum for different roles
    """

    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"
    ANNOUNCER = "announcer"


# -------- Link models
class ContestParticipant(SQLModel, table=True):
    """
    Link model for Contests <-> Participants many-to-many
    """

    participant_id: Optional[str] = Field(
        default=None, foreign_key="participant.id", primary_key=True
    )
    contest_id: Optional[str] = Field(
        default=None, foreign_key="contest.id", primary_key=True
    )


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
    features: List["Feature"] = Field(description="Required Features to Create")


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


# -------- Round Models


class ContestRoundBase(SQLModel, table=False):
    """
    Represents the state of the arena at a specific point in time.

    Maps to the ARENA_STATE entity in the ER diagram.
    """

    contest_id: str = Field(
        description="Reference to Contest", foreign_key="contest.id"
    )
    round_no: int = Field(description="Round number", ge=0)
    narrative: str = Field(default=None, description="Round narrative")
    state: ContestState = Field(description="Arena state")


class ContestRound(ContestRoundBase, DbBase, table=True):
    # relationships

    features: List["Feature"] = Relationship(back_populates="contestround")
    player_states: List["PlayerState"] = Relationship(back_populates="contestround")
    player_actions: List["PlayerAction"] = Relationship(back_populates="contestround")
    judge_results: List["JudgeResult"] = Relationship(back_populates="contestround")

    round_stats: "ContestRoundStats" = Relationship(
        back_populates="contestround", sa_relationship_kwargs={"uselist": False}
    )


class ContestRoundStatsBase(SQLModel, table=False):
    """
    Statistics for a round.

    Maps to the ROUND_STATS entity in the ER diagram.
    """

    contestround_id: str = Field(
        description="Reference to ArenaState", foreign_key="contestround.id"
    )
    actions_count: int = Field(description="Number of actions in the round")
    duration_ms: int = Field(description="Round duration in milliseconds")
    metrics_json: Dict = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Additional metrics as JSON",
    )


class ContestRoundStats(ContestRoundStatsBase, DbBase, table=True):
    """
    Represents the statistics for a specific contest round.

    Maps to the ROUND_STATS entity in the ER diagram.
    """

    contestround: ContestRound = Relationship(back_populates="round_stats")


# -------- Contest models


class ContestBase(SQLModel, table=False):
    """
    Represents a specific run of a contest between agents.

    Maps to the CONTEST entity in the ER diagram.
    """

    arena_id: str = Field(description="Reference to ArenaDTO", foreign_key="arena.id")
    current_round: int = Field(default=1, description="Current round")
    player_positions: str = Field(
        default="", description="A semicolon delimited list of player positions"
    )
    state: ContestState = Field(
        default=ContestState.CREATED, description="Contest state"
    )


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
        back_populates="contests", link_model=ContestParticipant
    )

    def participants_by_role(self):
        roles = {}
        for role in ParticipantRole:
            roles[role.value] = []
        for p in self.participants:
            roles[p.role.value] = p
        return roles


class ContestCreate(SQLModel, table=False):
    """
    This model is used by clients to kick off a new Contest with pre-defined objects.
    """

    arena_id: str = Field(description="Arena ID", foreign_key="arena.id")
    player_positions: str = Field(
        default=[], description="A semicolon delimited list of player positions"
    )
    participant_ids: List[str] = Field(
        description="IDs of Participants to load", foreign_key="participant.id"
    )


class ContestPublic(ContestBase, table=False):
    id: str


class ContestUpdate(ContestBase):
    pass


class FeatureBase(SQLModel, table=False):
    arena_id: Optional[str] = Field(
        default=None,
        description="Reference to Arena",
        foreign_key="arena.id",
    )
    contestround_id: Optional[str] = Field(
        default=None,
        description="Reference to a ContestRound",
        foreign_key="contestround.id",
    )
    name: str = Field(description="Feature name")
    description: str = Field(description="Feature description")
    position: str = Field(
        description="Grid coordinate as 'x,y'",
    )
    origin: FeatureOriginType = Field(description="Feature type")


class Feature(FeatureBase, DbBase, table=True):
    """
    Represents a feature in the arena DB.

    Maps to the FEATURE entity in the ER diagram.
    """

    arena: Arena = Relationship(back_populates="features")
    contestround: ContestRound = Relationship(back_populates="features")


class FeatureCreate(FeatureBase):
    """
    Request model for creating a feature
    """

    end_position: Optional[str] = Field(
        default=None,
        description="End coordinate for features with area",
    )


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
    origin: Optional[FeatureOriginType] = Field(
        default=None, description="Feature type"
    )
    end_position: Optional[str] = Field(
        default=None,
        description="End coordinate for features with area",
    )


class FeaturePublic(FeatureBase):
    id: str


# -------- Judge Results
class JudgeResultBase(SQLModel, table=False):
    """
    Represents the result of a judge's evaluation.

    Maps to the JUDGE_RESULT entity in the ER diagram.
    """

    contestround_id: str = Field(
        description="Contest Round identifier", foreign_key="contestround.id"
    )
    result: str = Field(description="Result description")
    reason: Optional[str] = Field(default=None, description="Reason for the result")


class JudgeResult(JudgeResultBase, DbBase, table=True):
    contestround: ContestRound = Relationship(back_populates="judge_results")


class JudgeResultCreate(JudgeResultBase):
    pass


# -------- Participant Models


class ParticipantBase(SQLModel, table=False):
    api_key: Optional[str] = Field(
        default=None,
        description="API key for authentication",
    )
    description: str = Field(
        default="",
        description="Agent description",
    )
    extra: Optional[Dict] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="Additional data",
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
    role: ParticipantRole = Field(
        description="Role in arena",
    )


class Participant(ParticipantBase, DbBase, table=True):
    """
    Maps agents to arenas
    """

    def url(self, path: str = ""):
        cleaned = urljoin(self.endpoint, path)
        return cleaned.replace("$ID$", self.id)

    contests: List[Contest] = Relationship(
        back_populates="participants", link_model=ContestParticipant
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
    role: Optional[ParticipantRole] = Field(default=None, description="Role in arena")


# --- Player models


class PlayerStateBase(SQLModel, table=False):
    """
    Represents the state of a player for a contest and round

    Maps to the PLAYER_STATE entity in the ER diagram.
    """

    participant_id: str = Field(
        description="Reference to Participant", foreign_key="participant.id"
    )
    contestround_id: str = Field(
        description="Reference to Contest Round", foreign_key="contestround.id"
    )
    position: str = Field(description="Grid coordinate as 'x,y'")
    inventory: Optional[List[str]] = Field(
        default_factory=List, sa_column=Column(JSON), description="Player inventory"
    )
    health_state: str = Field(description="Health state")
    extra: Optional[Dict] = Field(
        default_factory=Dict, sa_column=Column(JSON), description="Additional data"
    )


class PlayerState(PlayerStateBase, DbBase, table=True):
    contestround: ContestRound = Relationship(back_populates="player_states")


class PlayerStateCreate(PlayerStateBase, table=False):
    pass


# --- Player actions
class PlayerActionBase(SQLModel, table=False):
    """
    Represents an action taken by a player.

    Maps to the PLAYER_ACTION entity in the ER diagram.
    """

    participant_id: str = Field(
        description="Participant identifier", foreign_key="participant.id"
    )
    contestround_id: str = Field(
        description="contest round ref", foreign_key="contestround.id"
    )
    action: str = Field(description="Action description")
    target: Optional[str] = Field(
        default=None, description="Target coordinate as 'x,y'"
    )


class PlayerAction(PlayerActionBase, DbBase, table=True):
    contestround: ContestRound = Relationship(back_populates="player_actions")


class PlayerActionCreate(PlayerActionBase, table=False):
    pass
