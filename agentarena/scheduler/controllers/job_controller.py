from fastapi import APIRouter
from fastapi import Body
from sqlmodel import Field

from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobCreate
from agentarena.models.job import CommandJobPublic
from agentarena.models.job import CommandJobUpdate


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
        super().__init__(
            base_path=base_path,
            model_name="commandjob",
            model_service=model_service,
            model_public=CommandJobPublic,
            template_service=template_service,
            logging=logging,
        )

    def get_router(self):
        """
        Get the router for the job controller.
        Only exposes create and get endpoints.
        """
        self.log.info("getting job router")
        router = APIRouter(prefix=f"{self.base_path}/job", tags=[self.model_name])

        @router.post("/", response_model=CommandJobPublic)
        async def create(req: CommandJobCreate = Body(...)):
            with self.model_service.get_session() as session:
                return await self.create_model(req, session)

        @router.get("/{obj_id}", response_model=CommandJobPublic)
        async def get(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        return router
