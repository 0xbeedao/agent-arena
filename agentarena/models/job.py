"""
Provides models to manage aynchronous Jobs
"""

from datetime import datetime
from typing import Dict
from typing import List
from typing import Optional

from sqlmodel import JSON
from sqlmodel import Column
from sqlmodel import Field
from sqlmodel import Relationship
from sqlmodel import SQLModel

from agentarena.models.constants import JobState
from agentarena.models.dbbase import DbBase
from agentarena.models.public import CommandJobHistoryPublic
from agentarena.models.public import CommandJobPublic
from agentarena.models.public import UrlJobRequest


class CommandJobBase(SQLModel):

    parent_id: Optional[str] = Field(default=None, foreign_key="commandjob.id")
    channel: str = Field(description="channel for publishing")
    data: Optional[str] = Field(
        default=None,
        description="optional payload to send to Url (JSON string or empty string)",
    )
    method: str = Field(description="HTTP method, or MESSAGE")
    priority: int = Field(
        default=5, description="priority on a scale from 1 to 10, 10 high"
    )
    send_at: int = Field(
        default=0, description="Available in queue after what timestamp"
    )
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

    url: str = Field(description="Url to Call, or command channel for MESSAGE")


class CommandJob(CommandJobBase, DbBase, table=True):
    # Relationships
    parent: Optional["CommandJob"] = Relationship(
        back_populates="children",
        sa_relationship_kwargs={"remote_side": "CommandJob.id"},
    )
    children: List["CommandJob"] = Relationship(
        back_populates="parent",
        sa_relationship_kwargs={"remote_side": "CommandJob.parent_id"},
    )
    history: List["CommandJobHistory"] = Relationship(back_populates="job")

    def get_public(self) -> CommandJobPublic:
        return CommandJobPublic(
            id=self.id,
            channel=self.channel,
            data=self.data,
            method=self.method,
            priority=self.priority,
            send_at=self.send_at,
            state=self.state,
            started_at=self.started_at,
            finished_at=self.finished_at,
            parent_id=self.parent_id,
            url=self.url,
            history=[h.get_public() for h in self.history],
        )

    def make_child(self, req: UrlJobRequest) -> "CommandJob":
        """
        convenience method to make a child job
        """
        send_at = int(datetime.now().timestamp())
        if req.delay is not None and req.delay > 0:
            send_at += req.delay

        parent_priority = self.priority or 5
        priority = parent_priority - 1
        return CommandJob(
            id="",
            parent_id=self.id,
            parent=self,
            channel=req.channel or self.channel,
            data=req.data,
            method=req.method or self.method,
            priority=priority,
            send_at=send_at,
            state=JobState.IDLE,
            url=req.url or "",
        )


class CommandJobCreate(CommandJobBase):
    id: Optional[str] = Field(default="")


class CommandJobUpdate(SQLModel):
    channel: Optional[str] = Field(default=None, description="channel for publishing")
    data: Optional[Dict] = Field(
        default_factory=dict,
        sa_column=Column(JSON),
        description="optional payload to send to Url",
    )
    method: Optional[str] = Field(default=None, description="HTTP method, or MESSAGE")
    priority: Optional[int] = Field(
        default=None, description="priority on a scale from 1 to 10, 10 high"
    )
    send_at: Optional[int] = Field(
        default=None, description="Available in queue after what timestamp"
    )
    state: Optional[JobState] = Field(
        default=None, description="Job state, see JobState states"
    )
    started_at: Optional[int] = Field(
        default=None, description="When this job was picked up from queue"
    )
    finished_at: Optional[int] = Field(
        default=None, description="When this job was picked up from queue"
    )
    url: Optional[str] = Field(
        default=None, description="Url to Call, or command channel for MESSAGE"
    )


class CommandJobHistoryBase(SQLModel):
    job_id: str = Field(foreign_key="commandjob.id")
    from_state: JobState = Field(description="Original Job state, see JobState states")
    to_state: JobState = Field(description="Updated Job state, see JobState states")
    message: Optional[str] = Field(
        default="", description="Message associated with state change"
    )
    data: Optional[str] = Field(
        description="Optional JSON object returned from request",
    )


class CommandJobHistory(DbBase, CommandJobHistoryBase, table=True):
    job: CommandJob = Relationship(back_populates="history")

    def get_public(self) -> CommandJobHistoryPublic:
        return CommandJobHistoryPublic(
            id=self.id,
            job_id=self.job_id,
            from_state=self.from_state,
            to_state=self.to_state,
            message=self.message,
            data=self.data,
        )


class CommandJobHistoryCreate(CommandJobHistoryBase):
    pass


class CommandJobBatchRequest(SQLModel, table=False):
    batch: CommandJob = Field(
        description="The job to call when children are in final state"
    )
    children: List[UrlJobRequest] = Field(
        description="Child requests to be processed first"
    )


class GenerateJobBase(SQLModel):
    job_id: str = Field(description="external job ID foreign key")
    generated: Optional[str] = Field(
        default=None,
        description="The response data",
    )
    model: str = Field(description="model name")
    prompt: str = Field(description="Prompt to send")
    text: Optional[str] = Field(description="Generated text")
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
    pass


class GenerateJobCreate(GenerateJobBase, table=False):
    pass
