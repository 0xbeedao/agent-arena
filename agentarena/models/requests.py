"""
JSON serializable Request and Response models that don't have backing DTOs
"""

from typing import List
from typing import Optional

from pydantic import BaseModel
from sqlmodel import Field

from agentarena.models.constants import JobResponseState
from agentarena.models.constants import PromptType
from agentarena.models.public import ContestPublic
from agentarena.models.public import ContestRoundPublic
from agentarena.models.public import ParticipantPublic
from agentarena.models.public import PlayerActionPublic


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


class BaseParticipantRequest(BaseModel):
    """
    A request from the arena to a Participant
    """

    command: PromptType = Field(description="job command")
    # to be overridden by subclasses
    # data: str = Field(description="job payload")
    message: Optional[str] = Field(default="", description="message regarding data")
    state: Optional[JobResponseState] = Field(
        default=None, description="state of event, a JobState"
    )


class ContestRequestPayload(BaseModel):
    """
    A payload for a contest request
    """

    contest: ContestPublic


class ParticipantContestRequest(BaseParticipantRequest):
    """
    A participant request with a contest payload
    """

    data: ContestRequestPayload


class ActionRequestPayload(BaseModel):
    """
    A payload for an action request
    """

    contest: ContestPublic
    action: PlayerActionPublic
    player: ParticipantPublic


class ParticipantActionRequest(BaseParticipantRequest):
    """
    A participant request with an action payload
    """

    data: ActionRequestPayload


class ContestRoundPayload(BaseModel):
    """
    A payload for a contest round request
    """

    contest: ContestPublic
    round: ContestRoundPublic


class ParticipantContestRoundRequest(BaseParticipantRequest):
    """
    A participant request with a contest round payload
    """

    data: ContestRoundPayload
