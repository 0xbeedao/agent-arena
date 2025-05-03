"""
Arena configuration model for the Agent Arena application.
"""

from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .arenaagent import AgentRole, ArenaAgent, ArenaAgentRequest
from .dbmodel import DbBase
from .feature import Feature, FeatureRequest


class ArenaDTO(DbBase):
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
    agents: Optional[List[ArenaAgentRequest]] = Field(
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
    agents: List[ArenaAgent] = Field(
        default=None, description="Agents associated with the arena"
    )

    def agents_by_role(self) -> Dict[AgentRole, ArenaAgent]:
        """
        Returns a list of agents by their role.
        """
        # collect the agents by role
        agents_by_role = {
            AgentRole.ANNOUNCER: [],
            AgentRole.ARENA: [],
            AgentRole.JUDGE: [],
            AgentRole.PLAYER: [],
        }
        for agent in self.agents:
            if agent.role not in agents_by_role:
                raise f"Unknown agent role: {agent.role}"
            agents_by_role[agent.role].append(agent)
        return agents_by_role
