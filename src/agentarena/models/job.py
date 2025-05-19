"""
Provides models to manage aynchronous Jobs
"""

from datetime import datetime
from enum import Enum
from typing import Any
from typing import List
from typing import Mapping
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from agentarena.models.dbbase import DbBase


class JobState(Enum):
    IDLE = "idle"
    REQUEST = "request"
    RESPONSE = "response"
    WAITING = "waiting"
    FAIL = "fail"
    COMPLETE = "complete"


class JobResponseState(Enum):
    COMPLETED = "completed"
    PENDING = "pending"
    FAIL = "fail"


class JobResponse(BaseModel):
    job_id: str = Field(description="Job ID")
    delay: Optional[int] = Field(
        default=0, description="Request delay of x seconds before retry"
    )
    message: Optional[str] = Field(
        default="", description="Message regarding state, e.g. an error"
    )
    state: str = Field(
        description="JobResponseState field, one of ['completed', 'pending', 'fail']",
    )
    data: Any = Field(default={}, description="payload")
    # Not convinced I need this
    # child_data: Optional[List["JobResponse"]] = Field(
    #     default=[], description="child job responses"
    # )


class UrlJobRequest(BaseModel):
    command: str = Field(
        default="job.url.request",
        description="job command - this will be published as the subject on NATS",
    )
    data: Optional[Mapping[str, Any]] = Field(
        default={}, description="optional payload to send to Url"
    )
    delay: Optional[int] = Field(
        default=0, description="Request delay of x seconds before retry"
    )
    method: Optional[str] = Field(default="GET", description="HTTP method")
    url: Optional[str] = Field(description="Url to Call")


class CommandJob(DbBase):
    parent_id: Optional[str] = Field(
        default=None,
        description="The parent CommandJob, can be null, indicating this is a top-level job",
    )
    channel: str = Field(description="channel for publishing")
    data: Optional[Mapping[str, Any]] = Field(
        default={}, description="optional payload to send to Url"
    )
    method: str = Field(description="HTTP method, or MESSAGE")
    priority: Optional[int] = Field(
        default=5, description="priority on a scale from 1 to 10, 10 high"
    )
    send_at: int = Field(
        default=0, description="Available in queue after what timestamp"
    )
    state: Optional[str] = Field(
        default="idle", description="Job state, see JobState states"
    )
    started_at: int = Field(
        default=0, description="When this job was picked up from queue"
    )

    finished_at: int = Field(
        default=0,
        description="When this job reached a final state ['complete', 'fail', 'waiting']",
    )

    url: Optional[str] = Field(
        description="Url to Call, or command channel for MESSAGE"
    )

    def get_foreign_keys(self):
        return [("parent_id", "jobs", "id")]


class CommandJobHistory(DbBase):
    job_id: str = Field(description="Initiating job")
    from_state: str = Field(description="Original Job state, see JobState states")
    to_state: str = Field(description="Updated Job state, see JobState states")
    message: Optional[str] = Field(
        default="", description="Message associated with state change"
    )
    data: Optional[Mapping[str, Any]] = Field(
        default={}, description="Optional JSON object returned from request"
    )


class CommandJobRequest(BaseModel):
    """The JSON serializable request for a CommandJob"""

    id: str = Field(description="The Job ID")
    parent_id: Optional[str] = Field(
        default=None,
        description="The parent CommandJob, can be null, indicating this is a top-level job",
    )
    channel: str = Field(
        description="job command - this will be published as the subject on NATS"
    )
    data: Optional[Mapping[str, Any]] = Field(
        default={}, description="optional payload to send to Url"
    )
    method: str = Field(description="method, any HTTP method or 'MESSAGE' to use NATS")
    priority: Optional[int] = Field(
        default=5, description="priority on a scale from 1 to 10, 10 high"
    )
    send_at: int = Field(
        default=0, description="Available in queue after what timestamp"
    )
    state: Optional[str] = Field(
        default="idle", description="Job initial state, see JobState states"
    )
    url: Optional[str] = Field(description="Url to Call, or subject if using NATS")

    def make_child(self, req: UrlJobRequest) -> "CommandJobRequest":
        """
        convenience method to make a child job
        """
        send_at = int(datetime.now().timestamp())
        if req.delay is not None and req.delay > 0:
            send_at += req.delay

        parent_priority = self.priority or 5
        priority = parent_priority - 1
        return CommandJobRequest(
            id="",
            parent_id=self.id,
            channel=req.command or self.channel,
            data=req.data,
            method=req.method or self.method,
            priority=priority,
            send_at=send_at,
            state=JobState.IDLE.value,
            url=req.url,
        )

    def to_job(self) -> CommandJob:
        return CommandJob(
            id=self.id,
            parent_id=self.parent_id,
            channel=self.channel,
            data=self.data,
            method=self.method,
            priority=self.priority,
            send_at=self.send_at,
            state=self.state,
            url=self.url,
            started_at=0,
            finished_at=0,
        )


class CommandJobBatchRequest(BaseModel):
    batch: CommandJobRequest = Field(
        description="The job to call when children are in final state"
    )
    children: List[UrlJobRequest] = Field(
        description="Child requests to be processed first"
    )
