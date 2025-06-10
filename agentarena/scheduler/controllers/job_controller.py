import json

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from sqlmodel import Field
from sqlmodel import Session

from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.models.constants import JobState
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobCreate
from agentarena.models.job import CommandJobHistory
from agentarena.models.job import CommandJobHistoryCreate
from agentarena.models.job import CommandJobUpdate
from agentarena.models.public import CommandJobPublic


class JobController(
    ModelController[CommandJob, CommandJobCreate, CommandJobUpdate, CommandJobPublic]
):
    """
    Controller for managing CommandJob resources.
    Extends the ModelController with CommandJob as the type parameter.
    Exposes only create and get endpoints.
    """

    def __init__(
        self,
        base_path: str = "/api",
        model_service: ModelService[CommandJob, CommandJobCreate] = Field(
            description="The CommandJob model service"
        ),
        history_service: ModelService[
            CommandJobHistory, CommandJobHistoryCreate
        ] = Field(description="The CommandJobHistory model service"),
        template_service: JinjaRenderer = Field(description="The template service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """
        Initialize the job controller.

        Args:
            base_path: Base API path
            model_service: The CommandJob model service
            logging: Logging service
        """
        self.history_service = history_service
        super().__init__(
            base_path=base_path,
            model_name="commandjob",
            model_service=model_service,
            model_public=CommandJobPublic,
            template_service=template_service,
            logging=logging,
        )

    async def redo(self, job_id: str, session: Session, rekey: bool = False):
        """Clones a job to pending to run it again"""
        job = session.get(CommandJob, job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        data = job.data
        if rekey and data:
            self.log.info("rekeying job", job_id=job_id)
            work = json.loads(data)
            if "job_id" in work:
                work["job_id"] = self.model_service.uuid_service.make_id()
            self.log.info("new job id", job_id=work["job_id"])
            data = json.dumps(work)
        new_job = CommandJobCreate(
            id="",
            channel=job.channel,
            data=data,
            method=job.method,
            url=job.url,
            priority=job.priority,
            send_at=0,
            state=JobState.IDLE,
            started_at=0,
            finished_at=0,
        )
        new_job, result = await self.model_service.create(new_job, session)
        if not new_job or not result.success:
            raise HTTPException(status_code=500, detail="Failed to create job")
        self.log.info("job created", job_id=new_job.id)
        session.commit()
        return new_job.get_public()

    def get_router(self):
        """
        Get the router for the job controller.
        Only exposes create and get endpoints.
        """
        self.log.info("getting job router", path=self.base_path)
        router = APIRouter(prefix=self.base_path, tags=[self.model_name])

        @router.post("/", response_model=CommandJobPublic)
        async def create(req: CommandJobCreate = Body(...)):
            with self.model_service.get_session() as session:
                return await self.create_model(req, session)

        @router.get("/{obj_id}", response_model=CommandJobPublic)
        async def get(obj_id: str):
            self.log.info("getting job", obj_id=obj_id)
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        @router.post("/{obj_id}/redo", response_model=CommandJobPublic)
        async def redo(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.redo(obj_id, session, False)

        @router.post("/{obj_id}/redokey", response_model=CommandJobPublic)
        async def redo_key(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.redo(obj_id, session, True)

        return router
