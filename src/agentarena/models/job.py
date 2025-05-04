"""
Provides models to manage aynchronous Jobs
"""

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


class Job(DbBase):
    command: str = Field(description="job command")
    payload: str = Field(description="payload, usually JSON")
    caller: str = Field(description="Name of calling service")
    status: Optional[str] = Field(
        default="IDLE", description="Job status, see RequestMachine states"
    )
