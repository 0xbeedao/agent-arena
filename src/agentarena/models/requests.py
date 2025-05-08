"""
JSON serializable Request and Response models that don't have backing DTOs
"""

from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from agentarena.models.job import BaseAsyncJobResponse


class HealthStatus(BaseModel):
    """
    Represents the health of a responder/endpoint
    """

    name: str = Field(description="Responding service name")
    state: str = Field(description="state name, ['OK', <errorstate>]")
    version: Optional[str] = Field(default="", description="service version")


class HealthResponse(BaseAsyncJobResponse):
    """
    The wrapped async HealthResponse
    """

    data: HealthStatus = Field(description="Health Status response")
