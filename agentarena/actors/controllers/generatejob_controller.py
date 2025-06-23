from fastapi import BackgroundTasks
from fastapi import Body
from fastapi import HTTPException
from sqlmodel import Field
from sqlmodel import Session

from agentarena.actors.services.template_service import TemplateService
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.llm_service import LLMService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import GenerateJob
from agentarena.models.job import GenerateJobCreate
from agentarena.models.job import GenerateJobRepeat
from agentarena.models.public import GenerateJobPublic


class GenerateJobController(
    ModelController[
        GenerateJob, GenerateJobCreate, GenerateJobCreate, GenerateJobPublic
    ]
):
    def __init__(
        self,
        llm_service: LLMService = Field(),
        model_service: ModelService[GenerateJob, GenerateJobCreate] = Field(),
        template_service: TemplateService = Field(),
        uuid_service: UUIDService = Field(),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        super().__init__(
            base_path="/api/generatejob",
            model_name="generatejob",
            model_create=GenerateJobCreate,
            model_update=GenerateJobCreate,
            model_public=GenerateJobPublic,
            model_service=model_service,
            template_service=template_service,
            logging=logging,
        )
        self.llm_service = llm_service
        self.uuid_service = uuid_service

    async def repeat_job(
        self,
        req: GenerateJobRepeat,
        session: Session,
        background_tasks: BackgroundTasks,
    ) -> GenerateJobPublic:
        job, result = await self.model_service.get(req.original_id, session)
        if not job or not result.success:
            raise HTTPException(status_code=404, detail=result.model_dump())

        generate_job = GenerateJobCreate(
            job_id=self.uuid_service.make_id(),
            model=req.model or job.model,
            prompt=req.prompt or job.prompt,
            state=JobState.IDLE,
        )
        cloned, result = await self.model_service.create(generate_job, session)
        if not cloned or not result.success:
            self.log.error("error", result=result)
            raise HTTPException(status_code=404, detail=result.model_dump())
        self.log.info("cloned job", cloned=cloned.id, model=cloned.model)
        session.commit()

        background_tasks.add_task(self.llm_service.execute_job, cloned.id)

        return cloned.get_public()

    def get_router(self):
        router = super().get_router()

        @router.post("/repeat", response_model=GenerateJobPublic)
        async def repeat_job(
            background_tasks: BackgroundTasks, req: GenerateJobRepeat = Body(...)
        ):
            with self.model_service.get_session() as session:
                return await self.repeat_job(req, session, background_tasks)

        # @router.get("", response_model=List[GenerateJobPublic])
        # async def list_requests():
        #     with self.model_service.get_session() as session:
        #         return await self.get_model_list(session)

        # @router.get("/{job_id}.{format}", response_model=str)
        # async def get_md(job_id: str, format: str = "md"):
        #     with self.model_service.get_session() as session:
        #         return await self.get_model_with_format(job_id, session, format=format)

        # @router.get("/{job_id}", response_model=GenerateJobPublic)
        # async def get_job(job_id: str):
        #     with self.model_service.get_session() as session:
        #         return await self.get_model(job_id, session)

        return router
