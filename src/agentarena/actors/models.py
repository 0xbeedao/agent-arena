from enum import Enum
from sqlmodel import Column, Field
from urllib.parse import urljoin

from agentarena.models.dbbase import DbBase
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from sqlmodel import JSON
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

# ---- Link Models


class AgentStrategy(SQLModel, table=False):
    """
    Link Model for Agent <-> Strategy many-to-many
    """

    agent_id: str = Field(description="Agent", foreign_key="agent.id", primary_key=True)
    strategy_id: str = Field(
        description="Strategy", foreign_key="strategy.id", primary_key=True
    )


# ---- Agent Model


class AgentBase(SQLModel, table=False):
    """
    Configuration for an agent.

    Maps to the AGENT_CONFIG entity in the ER diagram.
    """

    name: str = Field(default="", description="Agent name")
    description: str = Field(default="", description="Agent description")
    endpoint: str = Field(default="", description="API endpoint for the agent")
    api_key: Optional[str] = Field(default="", description="API key for authentication")
    extra: Optional[Dict] = Field(
        default_factory=Dict, sa_column=Column(JSON), description="Additional data"
    )
    strategy_id: str = Field(foreign_key="strategy.id")

    def url(self, path: str = ""):
        return urljoin(self.endpoint, path)


class Agent(AgentBase, DbBase, table=True):
    # relationships
    strategy: "Strategy" = Relationship(back_populates="agents")


class AgentCreate(AgentBase, table=False):
    pass


class AgentUpdate(SQLModel, table=False):
    name: Optional[str] = Field(default=None, description="Agent name")
    description: Optional[str] = Field(default=None, description="Agent description")
    endpoint: Optional[str] = Field(
        default=None, description="API endpoint for the agent"
    )
    api_key: Optional[str] = Field(
        default=None, description="API key for authentication"
    )
    extra: Optional[Dict] = Field(
        default_factory=Dict, sa_column=Column(JSON), description="Additional data"
    )
    strategy_id: Optional[str] = Field(default=None, foreign_key="strategy.id")


class AgentPublic(AgentBase):
    id: str


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
    role: str = Field(default=StrategyType.PLAYER.value, description="Type of strategy")


class Strategy(StrategyBase, DbBase, table=True):
    agent: Agent = Relationship(back_populates="strategy")


class StrategyUpdate(SQLModel, table=False):
    """
    Represents a strategy that can be used by an agent.

    Maps to the STRATEGY entity in the ER diagram.
    """

    name: Optional[str] = Field(default=None, description="Strategy name")
    personality: Optional[str] = Field(
        default="", description="Personality description"
    )
    instructions: Optional[str] = Field(
        default=None, description="Strategy instructions"
    )
    description: Optional[str] = Field(
        default=None, description="Detailed description of the strategy"
    )
    role: Optional[str] = Field(default=None, description="Type of strategy")


#
