from enum import Enum

from pydantic import BaseModel
from pydantic import Field

from .dbbase import DbBase
from .strategy import Strategy


class ParticipantRole(str, Enum):
    """
    Enum for different roles
    """

    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"
    ANNOUNCER = "announcer"


class ParticipantDTO(DbBase):
    """
    Maps agents to arenas
    """

    arena_config_id: str = Field(description="Reference to ArenaDTO")
    agent_id: str = Field(description="Reference to Agent")
    role: str = Field(
        description="Role in arena"
    )  # note, str - enum is not supported in sqlite3

    def get_foreign_keys(self) -> list[tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("arena_config_id", "arenas", "id"), ("agent_id", "agents", "id")]


class ParticipantRequest(BaseModel):
    """
    Request model for creating a participant
    """

    agent_id: str = Field(description="Reference to Agent")
    role: ParticipantRole = Field(description="Role in arena")


class Participant(BaseModel):
    """
    Arena Agent model for the Agent Arena application.
    """

    id: str = Field(description="Participant ID")
    agent_id: str = Field(description="Reference to Agent")
    role: ParticipantRole = Field(description="Role in arena")
    name: str = Field(description="Agent name")
    description: str = Field(description="Agent description")
    strategy: Strategy = Field(description="Agent strategy")
