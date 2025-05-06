"""
Provides models to manage aynchronous Jobs
"""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel
from pydantic import Field

from agentarena.models.dbbase import DbBase


class BaseAsyncJobResponse(BaseModel):

    job_id: str = Field(description="ULID job ID")
    status: str = Field(
        default="complete",
        description="status field, one of ['completed', 'pending', 'failed']",
    )
    message: Optional[str] = Field(
        default="", description="Message regarding status, e.g. an error"
    )
    eta: Optional[int] = Field(
        default=0, description="Estimated time in milliseconds for job to complete"
    )


class JsonRequestJob(DbBase):
    caller: str = Field(description="Name of calling service")
    command: str = Field(description="job command")
    method: str = Field(desciption="HTTP method")
    payload: object = Field(description="JSON payload")
    attempt: int = Field(default=1, description="Request attempt counter")
    url: str = Field(description="Url to Call")
    send_at: Optional[datetime] = Field(
        default=None, description="Send after what timestamp"
    )
    status: Optional[str] = Field(
        default="IDLE", description="Job status, see RequestMachine states"
    )
