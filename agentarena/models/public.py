"""
Public Pydantic models - suitable for passing between apps, with no SQLModel stuff to accidentally cause tables to be created.
"""

from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from agentarena.models.constants import ContestRoundState
from agentarena.models.constants import ContestState
from agentarena.models.constants import JobResponseState
from agentarena.models.constants import JobState
from agentarena.models.constants import RoleType


class ArenaPublic(BaseModel):
    id: str = Field(default="", description="ID")
    name: str = Field(description="Arena name")
    description: str = Field(description="Arena description")
    height: int = Field(description="Arena height", gt=0)
    max_random_features: int = Field(description="maximum random features", default=0)
    width: int = Field(description="Arena width", gt=0)
    rules: str = Field(description="Game rules")
    winning_condition: str = Field(description="winning condition description")


class CommandJobPublic(BaseModel):
    id: str = Field(default="", description="ID")
    channel: str = Field(description="Channel")
    data: Optional[str] = Field(default=None, description="Data")
    method: str = Field(description="Method")
    priority: int = Field(description="Priority")
    send_at: int = Field(description="Timestamp")
    state: JobState = Field(description="Job state")
    started_at: int = Field(description="Timestamp")
    finished_at: Optional[int] = Field(default=None, description="Timestamp")
    parent_id: Optional[str] = Field(default=None, description="Parent job ID")
    url: str = Field(description="Url")
    history: List["CommandJobHistoryPublic"] = Field(default=[])


class CommandJobHistoryPublic(BaseModel):
    id: str = Field(default="", description="ID")
    job_id: str = Field(description="Job ID")
    from_state: JobState = Field(description="Original Job state")
    to_state: JobState = Field(description="Updated Job state")
    message: Optional[str] = Field(default=None, description="Message")
    data: Optional[str] = Field(default=None, description="Data")


class ContestPublic(BaseModel):
    id: str = Field(default="", description="ID")
    arena: ArenaPublic = Field()
    end_time: int = Field(description="Timestamp")
    participants: List["ParticipantPublic"] = Field(default=[])
    rounds: List["ContestRoundPublic"] = Field()
    start_time: int = Field(description="Timestamp")
    state: ContestState = Field(
        default=ContestState.CREATED, description="Contest state"
    )
    winner_id: Optional[str] = Field(default=None, description="ID of winning player")


class ContestRoundPublic(BaseModel):
    features: List["FeaturePublic"] = Field(default=[], description="Feature list")
    narrative: str = Field(default="", description="Round narrative")
    players: List["PlayerPublic"] = Field(default=[])
    round_no: int = Field(description="Round number", ge=0)
    state: ContestRoundState = Field(description="Round state")
    player_states: List["PlayerStatePublic"] = Field(
        default=[], description="Player states for this round"
    )
    player_actions: List["PlayerActionPublic"] = Field(
        default=[], description="Player actions for this round"
    )
    judge_results: List["JudgeResultPublic"] = Field(
        default=[], description="Judge results for this round"
    )


class FeaturePublic(BaseModel):
    description: str = Field(description="Feature description")
    name: str = Field(description="Feature name")
    position: str = Field(
        description="Grid coordinate as 'x,y'",
    )


class UrlJobRequest(BaseModel):
    channel: str = Field(
        default="job.url.request",
        description="job command - this will be published as the subject on NATS",
    )
    data: Optional[str] = Field(
        default=None,
        description="optional payload to send to Url",
    )
    delay: Optional[int] = Field(
        default=0, description="Request delay of x seconds before retry"
    )
    method: Optional[str] = Field(default="GET", description="HTTP method")
    url: Optional[str] = Field(description="Url to Call")


class JobResponse(UrlJobRequest):
    job_id: str = Field(description="Job ID")
    message: Optional[str] = Field(
        default="", description="Message regarding state, e.g. an error"
    )
    state: JobResponseState = Field(
        description="JobResponseState field, one of ['completed', 'pending', 'fail']",
    )
    child_data: Optional[List["JobResponse"]] = Field(
        default_factory=list,
        description="child job responses",
    )
    url: Optional[str] = Field(default="")


class ModelChangeMessage(BaseModel):
    """
    Message sent to the controller when a model changes.
    """

    action: str = Field(description="Action that triggered the change")
    model_id: str = Field(description="ID of the changed model")
    detail: Optional[str] = Field(default="", description="Details about the change")


class ParticipantPublic(BaseModel):
    id: str = Field(default="", description="ID")
    description: str = Field(
        default="",
        description="Agent description",
    )
    endpoint: str = Field(
        default="",
        description="API endpoint for the agent",
    )
    name: str = Field(
        description="Participant name",
        max_length=100,
        min_length=1,
    )
    role: RoleType = Field(
        description="Role in arena",
    )


class PlayerPublic(BaseModel):
    id: str = Field()
    name: str = Field()
    position: str = Field(description="x,y position")
    inventory: List[str] = Field(default=[], description="Player inventory")
    health: str = Field(default="Fresh", description="description of player health")
    score: int = Field(default=0, description="game score")
    memories: Optional[str] = Field(
        default="", description="Player memories for this round"
    )


class PlayerStatePublic(BaseModel):
    participant_id: str = Field(description="Reference to Participant")
    position: str = Field(description="Grid coordinate as 'x,y'")
    inventory: List[str] = Field(default=[], description="Player inventory")
    health: str = Field(default="Fresh", description="Health state")
    score: int = Field(default=0, description="game score on a scale of 0-100")


class PlayerActionPublic(BaseModel):
    participant_id: str = Field(description="Participant identifier")
    action: str = Field(description="Action description")
    narration: str = Field(description="Narration to share with other players")
    memories: str = Field(description="Private memories not shared with other players")
    target: str = Field(description="Target coordinate as 'x,y'")


class JudgeResultPublic(BaseModel):
    result: str = Field(description="Result description")
    reason: str = Field(default="", description="Reason for the result")
    memories: str = Field(description="Private memories not shared with players")
    narration: str = Field(description="Narration to share with other players")
