"""
Provides models to manage aynchronous Jobs
"""

from datetime import datetime
from enum import Enum
from typing import Any
from typing import List
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from agentarena.models.dbbase import DbBase


class JobCommandType(Enum):
    REQUEST = "request"
    BATCH = "batch"


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
    job_id: str = Field(description="ULID job ID")
    delay: Optional[int] = Field(
        default=0, description="Request delay of x seconds before retry"
    )
    message: Optional[str] = Field(
        default="", description="Message regarding state, e.g. an error"
    )
    state: str = Field(
        description="state field, one of ['completed', 'pending', 'fail']",
    )
    data: Optional[Any] = Field(default="", description="payload")


class JsonRequestSummary(BaseModel):
    url: Optional[str] = Field(description="Url to Call")
    event: Optional[str] = Field(default="", description="Event to send on complete")
    method: Optional[str] = Field(default="GET", description="HTTP method")
    data: Optional[str] = Field(description="optional payload to send to Url")
    delay: Optional[int] = Field(
        default=0, description="Request delay of x seconds before retry"
    )


class CommandJob(DbBase):
    parent_id: Optional[str] = Field(
        default=None,
        description="The parent CommandJob, can be null, indicating this is a top-level job",
    )
    command: str = Field(description="job command: batch, request")
    data: Optional[str] = Field(description="optional payload to send to Url")
    event: Optional[str] = Field(
        default="", description="Optional event name to throw when complete"
    )
    method: str = Field(description="HTTP method")
    priority: Optional[int] = Field(
        default=5, description="priority on a scale from 1 to 10, 10 high"
    )
    send_at: int = Field(
        default=0, description="Available in queue after what timestamp"
    )
    state: Optional[str] = Field(
        default="idle", description="Job state, see JobState states"
    )
    started_at: int = (
        Field(default=0, description="When this job was picked up from queue"),
    )
    finished_at: int = (
        Field(
            default=0,
            description="When this job reached a final state ['complete', 'fail', 'waiting']",
        ),
    )
    url: Optional[str] = Field(description="Url to Call")

    def get_foreign_keys(self):
        return [("parent_id", "jobs", "id")]

    def make_child(self, req: JsonRequestSummary) -> "CommandJob":
        """
        convenience method to make a child job
        """
        send_at = int(datetime.now().timestamp())
        if req.delay > 0:
            send_at += req.delay
        return CommandJob(
            parent_id=self.id,
            command=JobCommandType.REQUEST.value,
            data=req.data,
            event=req.event,
            method=req.method,
            priority=self.priority,
            send_at=send_at,
            state=JobState.IDLE.value,
            started_at=0,
            finished_at=0,
            url=req.url,
        ).fill_defaults()

    def make_batch_requests(
        self, requests: List[JsonRequestSummary]
    ) -> List["CommandJob"]:
        """ """
        return [self.make_child(req) for req in requests]


class CommandJobHistory(DbBase):
    job_id: str = Field(description="Initiating job")
    from_state: str = Field(description="Original Job state, see JobState states")
    to_state: str = Field(description="Updated Job state, see JobState states")
    message: Optional[str] = Field(
        default="", description="Message associated with state change"
    )
    data: Optional[str] = Field(
        default="", description="Optional JSON object returned from request"
    )
