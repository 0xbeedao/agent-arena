"""
Provides models to manage aynchronous Jobs
"""

from typing import Optional

from sqlmodel import Field
from sqlmodel import SQLModel

from agentarena.models.constants import JobState
from agentarena.models.constants import PromptType
from agentarena.models.dbbase import DbBase
from agentarena.models.public import GenerateJobPublic


class GenerateJobBase(SQLModel):
    job_id: str = Field(description="external job ID foreign key")
    prompt_type: PromptType = Field(description="Prompt type")
    generated: Optional[str] = Field(
        default=None,
        description="The response data",
    )
    model: str = Field(description="model name")
    prompt: str = Field(description="Prompt to send")
    state: JobState = Field(
        default=JobState.IDLE, description="Job state, see JobState states"
    )
    started_at: int = Field(
        default=0, description="When this job was picked up from queue"
    )

    finished_at: int = Field(
        default=0,
        description="When this job reached a final state ['complete', 'fail', 'waiting']",
    )


class GenerateJob(GenerateJobBase, DbBase, table=True):

    def get_public(self) -> GenerateJobPublic:
        return GenerateJobPublic(
            id=self.id,
            job_id=self.job_id,
            generated=self.generated,
            model=self.model,
            prompt=self.prompt,
            prompt_type=self.prompt_type.value,
            state=self.state,
            started_at=self.started_at,
            finished_at=self.finished_at,
        )


class GenerateJobRepeat(SQLModel, table=False):
    """Used to repeat a generate job"""

    original_id: str = Field(description="The original job ID")
    prompt: Optional[str] = Field(default=None, description="The prompt to send")
    model: Optional[str] = Field(default=None, description="The model to use")


class GenerateJobCreate(GenerateJobBase, table=False):
    pass


class JobLock(DbBase, table=True):
    ttl: int = Field(default=600, description="Time to live in seconds")
