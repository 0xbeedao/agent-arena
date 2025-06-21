from typing import List
from sqlmodel import Field
from agentarena.actors.services.template_service import TemplateService
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import GenerateJob
from agentarena.models.job import GenerateJobCreate
from agentarena.models.public import GenerateJobPublic
from agentarena.core.services.model_service import ModelService


class GenerateJobController(
    ModelController[
        GenerateJob, GenerateJobCreate, GenerateJobCreate, GenerateJobPublic
    ]
):
    def __init__(
        self,
        model_service: ModelService[GenerateJob, GenerateJobCreate] = Field(),
        template_service: TemplateService = Field(),
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

    def get_router(self):
        router = super().get_router()

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
