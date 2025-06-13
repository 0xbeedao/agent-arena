"""
Arena configuration model for the Agent Arena application.
"""

from enum import Enum
from typing import Dict
from typing import List
from typing import Optional

from sqlmodel import JSON
from sqlmodel import Column
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import ContestState
from agentarena.models.constants import RoleType
from agentarena.models.dbbase import DbBase
from agentarena.models.public import ArenaPublic
from agentarena.models.public import ContestPublic
from agentarena.models.public import ContestRoundPublic
from agentarena.models.public import FeaturePublic
from agentarena.models.public import ParticipantPublic
from agentarena.models.public import PlayerPublic
from agentarena.models.public import PlayerStatePublic
from agentarena.models.public import PlayerActionPublic
from agentarena.models.public import JudgeResultPublic


class FeatureOriginType(str, Enum):
    """
    Enum for feature types.
    """

    REQUIRED = "required"
    RANDOM = "random"


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
    contests: List["Contest"] = Relationship(back_populates="arena")

    def get_public(self) -> ArenaPublic:
        return ArenaPublic(
            id=self.id,
            name=self.name,
            description=self.description,
            height=self.height,
            width=self.width,
            rules=self.rules,
            max_random_features=self.max_random_features,
            winning_condition=self.winning_condition,
        )


class ArenaCreate(ArenaBase):
    features: List["Feature"] = Field(description="Required Features to Create")


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
    state: ContestRoundState = Field(description="Round state")


class ContestRound(ContestRoundBase, DbBase, table=True):
    # relationships

    contest: "Contest" = Relationship(
        back_populates="rounds",
        sa_relationship_kwargs={"uselist": False},
    )
    features: List["Feature"] = Relationship(back_populates="contestround")
    judge_results: List["JudgeResult"] = Relationship(back_populates="contestround")
    player_states: List["PlayerState"] = Relationship(back_populates="contestround")
    player_actions: List["PlayerAction"] = Relationship(back_populates="contestround")
    round_stats: "ContestRoundStats" = Relationship(
        back_populates="contestround",
        sa_relationship_kwargs={"uselist": False},
    )

    def get_public(self) -> ContestRoundPublic:
        players = []
        for p in self.player_states:
            possibles = [
                x for x in self.player_actions if x.participant_id == p.participant_id
            ]
            pa = possibles[0] if possibles else None
            possibles = [
                x for x in self.judge_results if x.participant_id == p.participant_id
            ]
            jr = possibles[0] if possibles else None
            players.append(
                PlayerPublic(
                    id=p.participant_id,
                    name=p.participant.name,
                    position=p.position,
                    inventory=p.inventory,
                    health=p.health,
                    score=p.score,
                    action=pa.get_public() if pa else None,
                    result=jr.get_public() if jr else None,
                )
            )
        return ContestRoundPublic(
            features=[f.get_public() for f in self.features],
            round_no=self.round_no,
            players=players,
            state=self.state,
            narrative=self.narrative,
        )


class ContestRoundCreate(ContestRoundBase):
    pass


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
    current_round: int = Field(default=0, description="Current round")
    player_inventories: str = Field(
        default="[]",
        description="Json for a list of lists of player inventories",
    )
    player_positions: str = Field(
        default="[]",
        description="Json for a list of starting player positions",
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

    arena: "Arena" = Relationship(
        back_populates="contests",
        sa_relationship_kwargs={"uselist": False},
    )
    participants: List["Participant"] = Relationship(
        back_populates="contests", link_model=ContestParticipant
    )
    rounds: List["ContestRound"] = Relationship(
        back_populates="contest",
        sa_relationship_kwargs={"order_by": "ContestRound.round_no"},
    )
    winner: Optional["Participant"] = Relationship()

    def participants_by_role(self):
        roles = {}
        for role in RoleType:
            roles[role.value] = []
        for p in self.participants:
            roles[p.role.value].append(p)
        return roles

    def get_public(self):
        return ContestPublic(
            id=self.id,
            arena=self.arena.get_public(),
            participants=[p.get_public() for p in self.participants],
            rounds=[r.get_public() for r in self.rounds],
            start_time=self.start_time or 0,
            end_time=self.end_time or 0,
            state=self.state,
            winner_id=self.winner_id,
        )

    def get_role(self, role: RoleType):
        """
        Returns a list of participants filtered by their role.
        """
        return [p for p in self.participants if p.role == role]


class ContestCreate(SQLModel, table=False):
    """
    This model is used by clients to kick off a new Contest with pre-defined objects.
    """

    arena_id: str = Field(description="Arena ID", foreign_key="arena.id")
    player_positions: str = Field(
        default=[], description="Json for a list of player x,y positions"
    )
    player_inventories: str = Field(
        default=[], description="Json for a list of lists of player inventories"
    )
    participant_ids: List[str] = Field(
        description="IDs of Participants to load", foreign_key="participant.id"
    )


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

    def get_public(self) -> FeaturePublic:
        return FeaturePublic(
            description=self.description, name=self.name, position=self.position
        )


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


# -------- Judge Results
class JudgeResultBase(SQLModel, table=False):
    """
    Represents the result of a judge's evaluation.

    Maps to the JUDGE_RESULT entity in the ER diagram.
    """

    contestround_id: str = Field(
        description="Contest Round identifier", foreign_key="contestround.id"
    )
    participant_id: str = Field(
        description="Participant identifier", foreign_key="participant.id"
    )
    narration: str = Field(description="Narration to share with other players")
    memories: str = Field(description="Private memories not shared with players")
    result: str = Field(description="Result description")
    reason: str = Field(default="", description="Reason for the result")


class JudgeResult(JudgeResultBase, DbBase, table=True):
    contestround: ContestRound = Relationship(back_populates="judge_results")

    def get_public(self) -> JudgeResultPublic:
        return JudgeResultPublic(
            result=self.result,
            reason=self.reason,
            narration=self.narration,
            memories=self.memories,
        )


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


class Participant(ParticipantBase, DbBase, table=True):
    """
    Maps agents to arenas
    """

    def url(self, path: str = ""):
        cleaned = self.endpoint.replace("$ID$", self.id or "unknown")
        if not cleaned.endswith("/"):
            cleaned += "/"
        return f"{cleaned}{path}"

    contests: List[Contest] = Relationship(
        back_populates="participants", link_model=ContestParticipant
    )

    def get_public(self) -> ParticipantPublic:
        return ParticipantPublic(
            id=self.id, description=self.description, name=self.name, role=self.role
        )


class ParticipantCreate(ParticipantBase):
    """
    Request model for creating a participant
    """


class ParticipantUpdate(SQLModel):
    """
    Request model for creating a participant
    """

    arena_id: Optional[str] = Field(
        default=None, description="Reference to ArenaDTO", foreign_key="arena.id"
    )
    name: Optional[str] = Field(default=None, description="Participant name")
    role: Optional[RoleType] = Field(default=None, description="Role in arena")


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
    inventory: List[str] = Field(
        default_factory=List, sa_column=Column(JSON), description="Player inventory"
    )
    health: str = Field(default="Fresh", description="Health state")
    score: int = Field(default=0, description="game score on a scale of 0-100")


class PlayerState(PlayerStateBase, DbBase, table=True):
    contestround: ContestRound = Relationship(back_populates="player_states")
    participant: Participant = Relationship()

    def get_public(self) -> PlayerStatePublic:
        return PlayerStatePublic(
            name=self.participant.name,
            participant_id=self.participant_id,
            position=self.position,
            inventory=self.inventory,
            health=self.health,
            score=self.score,
        )


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
    narration: str = Field(description="Narration to share with other players")
    memories: str = Field(description="Private memories not shared with other players")
    target: str = Field(
        description="Target coordinate as 'x,y', else name of feature or player"
    )


class PlayerAction(PlayerActionBase, DbBase, table=True):
    contestround: ContestRound = Relationship(back_populates="player_actions")
    player: Participant = Relationship()

    def get_public(self) -> PlayerActionPublic:
        return PlayerActionPublic(
            participant_id=self.participant_id,
            action=self.action,
            narration=self.narration,
            memories=self.memories,
            target=self.target,
        )


class PlayerActionCreate(PlayerActionBase, table=False):
    pass


# --- Requests
