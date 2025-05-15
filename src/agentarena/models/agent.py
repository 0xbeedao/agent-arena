"""
Agent configuration model for the Agent Arena application.
"""

import urllib.parse
from typing import Optional

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

    def url(self, path: str = ""):
        return urllib.parse.urljoin(self.endpoint, path)
