from enum import Enum
from typing import List
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

from agentarena.models.dbbase import DbBase

# ---- Link Models


# ---- Agent Model


class AgentBase(SQLModel, table=False):
    """
    Configuration for an agent participant.

    Maps to the AGENT_CONFIG entity in the ER diagram.
    """

    name: str = Field(
        default="",
        description="Name of the agent participant - should match the participant name",
    )
    strategy_id: str = Field(foreign_key="strategy.id")


class Agent(AgentBase, DbBase, table=True):
    # relationships
    strategy: "Strategy" = Relationship(back_populates="agents")


class AgentCreate(AgentBase, table=False):
    pass


class AgentUpdate(SQLModel, table=False):
    participant_id: Optional[str] = Field(
        default=None,
        foreign_key="participant.id",
        description="ID of the participant",
    )
    strategy_id: Optional[str] = Field(
        default=None,
        foreign_key="strategy.id",
    )


class AgentPublic(AgentBase, table=False):
    """
    Public representation of an Agent.
    """

    id: str = Field(default=None, description="Unique identifier for the Agent")


# ---- Strategy models


class StrategyType(Enum):
    """
    Enum for different strategy types.
    """

    JUDGE = "judge"
    ARENA = "arena"
    PLAYER = "player"
    ANNOUNCER = "announcer"


class StrategyBase(SQLModel, table=False):
    """
    Represents a strategy that can be used by an agent.

    Maps to the STRATEGY entity in the ER diagram.
    """

    name: str = Field(default="", description="Strategy name")
    personality: str = Field(default="", description="Personality description")
    instructions: str = Field(default="", description="Strategy instructions")
    description: str = Field(
        default="", description="Detailed description of the strategy"
    )
    role: StrategyType = Field(
        default=StrategyType.PLAYER, description="Type of strategy"
    )


class Strategy(StrategyBase, DbBase, table=True):
    participants: List["Agent"] = Relationship(back_populates="strategy")
    agents: List[Agent] = Relationship(
        back_populates="strategy",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )


class StrategyUpdate(SQLModel, table=False):
    """
    Represents a strategy that can be used by an agent.

    Maps to the STRATEGY entity in the ER diagram.
    """

    name: Optional[str] = Field(default=None, description="Strategy name")
    personality: Optional[str] = Field(
        default=None, description="Personality description"
    )
    instructions: Optional[str] = Field(
        default=None, description="Strategy instructions"
    )
    description: Optional[str] = Field(
        default=None, description="Detailed description of the strategy"
    )
    role: Optional[str] = Field(default=None, description="Type of strategy")


class StrategyCreate(StrategyBase):
    pass


class StrategyPublic(StrategyBase):
    id: str


#
