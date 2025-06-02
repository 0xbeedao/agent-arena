"""
JSON serializable Request and Response models that don't have backing DTOs
"""

from typing import List
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field

from agentarena.models.constants import JobResponseState
from agentarena.models.constants import PromptType
from agentarena.models.public import ArenaPublic
from agentarena.models.public import ContestPublic
from agentarena.models.public import FeaturePublic
from agentarena.models.public import ParticipantPublic


class ControllerRequest(BaseModel):
    """
    Base model for requests to the controller.
    """

    action: str = Field(description="Action to perform")
    data: Optional[str] = Field(
        default="", description="Additional JSON data for the action"
    )
    target_id: Optional[str] = Field(default="", description="Contest ID if applicable")
    subjects: Optional[List[str]] = Field(
        default=[], description="Arena ID if applicable"
    )


class HealthStatus(BaseModel):
    """
    Represents the health of a responder/endpoint
    """

    name: str = Field(description="Responding service name")
    state: str = Field(description="state name, ['OK', <errorstate>]")
    version: Optional[str] = Field(default="", description="service version")


class ParticipantRequest(BaseModel):
    """
    A request from the arena to a Participant
    """

    job_id: str = Field(description="job that caused this event")
    command: PromptType = Field(description="job command")
    data: str = Field(description="job payload")
    message: Optional[str] = Field(default="", description="message regarding data")
    state: Optional[JobResponseState] = Field(
        default=None, description="state of event, a JobState"
    )


class PlayerActionRequest(BaseModel):
    """
    Model sent to Players for action requests, as JSON in the data field
    """

    player: ParticipantPublic = Field()
    arena: ArenaPublic = Field()
    contest: ContestPublic = Field()
    features: List[FeaturePublic] = Field()
    players: List[ParticipantPublic] = Field()
    round_no: int = Field()
