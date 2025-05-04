"""
Agent configuration model for the Agent Arena application.
"""

from typing import List
from typing import Optional
from typing import Tuple

from pydantic import Field

from .dbbase import DbBase


class AgentDTO(DbBase):
    """
    Configuration for an agent.

    Maps to the AGENT_CONFIG entity in the ER diagram.
    """

    name: Optional[str] = Field(default="", description="Agent name")
    description: Optional[str] = Field(default="", description="Agent description")
    endpoint: Optional[str] = Field(
        default="", description="API endpoint for the agent"
    )
    api_key: Optional[str] = Field(default="", description="API key for authentication")
    metadata: Optional[str] = Field(default="", description="Additional metadata")
    strategy_id: Optional[str] = Field(
        default="", description="Reference to StrategyDTO"
    )

    def get_foreign_keys(self) -> List[Tuple[str, str, str]]:
        """
        Returns the foreign keys for this model.
        """
        return [("strategy_id", "strategies", "id")]
