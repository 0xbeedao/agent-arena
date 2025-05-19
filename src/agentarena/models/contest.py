"""
Contest model for the Agent Arena application.
"""

from enum import Enum
from typing import List
from typing import Optional
from typing import Tuple

from pydantic import BaseModel
from pydantic import Field

from agentarena.models.arena import Arena
from agentarena.models.participant import Participant

from .dbbase import DbBase


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


class ContestDTO(DbBase, table=True):
    """
    Represents a contest between agents.

    Maps to the CONTEST entity in the ER diagram.
    """

    arena_config_id: str = Field(description="Reference to ArenaDTO")
    current_round: int = Field(default=1, description="Current round")
    player_positions: str = Field(
        description="A semicolon delimited list of player positions"
    )
    state: str = (
        Field(default=ContestState.CREATED.value, description="Contest state"),
    )
    winner: Optional[str] = Field(
        default=None, description="id of winning player agent"
    )

    start_time: Optional[int] = Field(default=None, description="Contest start time")
    end_time: Optional[int] = Field(default=None, description="Contest end time")

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("arena_config_id", "arenas", "id")]


class ContestAgentDTO(DbBase, table=True):
    """
    Maps agents to contests
    """

    role: str = Field(description="Role in contest")
    contest_id: str = Field(description="Reference to a Contest")
    agent_id: str = Field(description="Reference to the Agent playing this role")

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("contest_id", "contests", "id"), ("agent_id", "agents", "id")]


class ContestAgentRequest(BaseModel):
    """
    Request model for creating a contest agent
    """

    role: ContestRole = Field(description="Role in contest")
    agent_id: str = Field(description="Reference to the Agent playing this role")


class ContestRequest(BaseModel):
    """
    Request model for creating a contest
    """

    arena_config_id: str = Field(description="Reference to ArenaDTO")
    current_round: Optional[int] = Field(default=1, description="Current round")
    player_positions: List[str] = Field(
        description="Positions to use for players, must be at least as long as the number of players"
    )


class Contest(BaseModel):
    """
    Contest model for the Agent Arena application.

    Maps to the CONTEST entity in the ER diagram.
    """

    id: str = Field(description="Contest identifier")
    arena: Arena = Field(description="Arena")
    current_round: int = Field(description="Current round number")
    player_positions: List[str] = Field(
        description="A list of positions of players at start"
    )
    state: ContestState = Field(description="Contest state")
    start_time: Optional[int] = Field(default=None, description="Contest start time")
    end_time: Optional[int] = Field(default=None, description="Contest end time")
    winner: Optional[Participant] = Field(description="winning player")
