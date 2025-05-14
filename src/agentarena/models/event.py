from typing import Any
from typing import Optional

from pydantic import Field

from agentarena.models.dbbase import DbBase
from agentarena.models.job import CommandJob
from agentarena.models.job import JobCommandType
from agentarena.models.job import JobResponse
from agentarena.models.job import JobResponseState


class JobEvent(DbBase):
    job_id: str = Field(description="job that caused this event")
    command: str = Field(description="job command")
    data: Any = Field(description="job payload")
    message: Optional[str] = Field(description="message regarding data")
    state: str = Field(description="state of event, a JobState")

    @staticmethod
    def from_job_and_response(job: CommandJob, response: JobResponse):
        if response is None:
            response = JobResponse(
                job_id=job.id,
                data="",
                command=JobCommandType.REQUEST.value,
                message="",
                state=JobResponseState.COMPLETED.value,
            )
        return JobEvent(
            job_id=job.id,
            data=response.data,
            command=job.command,
            message=response.message,
            state=response.state,
        )
