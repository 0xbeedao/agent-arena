"""
Provides models to manage aynchronous Jobs
"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional

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


class BaseAsyncJobResponse(BaseModel):
    job_id: str = Field(description="ULID job ID")
    eta: Optional[int] = Field(
        default=0, description="Estimated time in milliseconds for job to complete"
    )
    message: Optional[str] = Field(
        default="", description="Message regarding state, e.g. an error"
    )
    state: str = Field(
        description="state field, one of ['completed', 'pending', 'fail']",
    )
    data: Optional[Any] = Field(default="", description="payload")


class JsonRequestJob(DbBase):
    attempt: int = Field(default=1, description="Request attempt counter")
    caller: str = Field(description="Name of calling service")
    command: str = Field(description="job command")
    method: str = Field(description="HTTP method")
    original_job: Optional[str] = Field(
        default="", description="link to original job id for retries"
    )
    payload: object = Field(description="JSON payload")
    priority: Optional[int] = Field(
        default=5, description="priority on a scale from 1 to 10, 10 high"
    )
    final_message: Optional[str] = Field(
        default="", description="Message sent with final state change"
    )
    finished_at: int = (
        Field(
            default=0,
            description="When this job reached a final state ['complete', 'fail', 'waiting']",
        ),
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
    url: str = Field(description="Url to Call")

    def make_attempt(self):
        return JsonRequestJob(
            attempt=self.attempt + 1,
            caller=self.caller,
            command=self.command,
            method=self.method,
            original_job=self.id,
            payload=self.payload,
            priority=self.priority,
            send_at=int(datetime.now().timestamp()),
            state=JobState.IDLE.value,
            url=self.url,
        )
