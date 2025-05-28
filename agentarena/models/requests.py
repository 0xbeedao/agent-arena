"""
JSON serializable Request and Response models that don't have backing DTOs
"""

from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field


class HealthStatus(BaseModel):
    """
    Represents the health of a responder/endpoint
    """

    name: str = Field(description="Responding service name")
    state: str = Field(description="state name, ['OK', <errorstate>]")
    version: Optional[str] = Field(default="", description="service version")
