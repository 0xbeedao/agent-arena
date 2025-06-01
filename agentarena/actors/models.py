from typing import List
from typing import Optional

from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

from agentarena.models import constants
from agentarena.models.constants import PromptType
from agentarena.models.constants import RoleType
from agentarena.models.dbbase import DbBase

# ---- Agent Model


class AgentBase(SQLModel, table=False):
    """
    Configuration for an agent participant.

    Maps to the AGENT_CONFIG entity in the ER diagram.
    """

    model: str = Field(
        default=constants.DEFAULT_AGENT_MODEL,
        description="LLM model name or alias",
    )
    name: str = Field(
        default="",
        description="Name of the agent participant - should match the participant name",
    )
    participant_id: str = Field(
        description="ID of the participant, NOT a foreign key, because this is a separate database",
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


class StrategyBase(SQLModel, table=False):
    """
    Represents a strategy that can be used by an agent.

    Maps to the STRATEGY entity in the ER diagram.
    """

    name: str = Field(default="", description="Strategy name")
    personality: str = Field(default="", description="Personality description")
    description: str = Field(
        default="", description="Detailed description of the strategy"
    )
    role: RoleType = Field(default=RoleType.PLAYER, description="Type of strategy")


class Strategy(StrategyBase, DbBase, table=True):
    agents: List[Agent] = Relationship(
        back_populates="strategy",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"},
    )
    agents: List["Agent"] = Relationship(back_populates="strategy")
    prompts: List["StrategyPrompt"] = Relationship(back_populates="strategy")


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
    prompts: List["StrategyPromptCreate"] = Field(description="List of prompts by key")


class StrategyPublic(StrategyBase):
    id: str


class StrategyPromptBase(SQLModel, table=False):
    strategy_id: str = Field(foreign_key="strategy.id")
    prompt: str = Field(description="Prompt text")
    key: PromptType = Field()


class StrategyPrompt(StrategyPromptBase, DbBase, table=True):
    strategy: Strategy = Relationship(back_populates="prompts")


class StrategyPromptCreate(SQLModel, table=False):
    prompt: str = Field()
    key: PromptType = Field()


class StrategyPromptPublic(StrategyPromptBase, table=False):
    id: str = Field()
