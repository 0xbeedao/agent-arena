from fastapi import APIRouter
from fastapi import Body
from pydantic import Field

from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.job import CommandJob
from agentarena.core.services.model_service import ModelService


class JobController(ModelController[CommandJob]):
    """
    Controller for managing CommandJob resources.
    Extends the ModelController with CommandJob as the type parameter.
    Exposes only create and get endpoints.
    """

    def __init__(
        self,
        base_path: str = "/api",
        model_service: ModelService[CommandJob] = Field(
            description="The CommandJob model service"
        ),
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
            model_name="job",
            model_service=model_service,
            logging=logging,
        )

    def get_router(self):
        """
        Get the router for the job controller.
        Only exposes create and get endpoints.
        """
        self.log.info("getting job router")
        router = APIRouter(prefix=self.base_path, tags=[self.model_name])

        @router.post("/", response_model=CommandJob)
        async def create(req: CommandJob = Body(...)):
            return await self.create_model(req)

        @router.get("/{obj_id}", response_model=CommandJob)
        async def get(obj_id: str):
            return await self.get_model(obj_id)

        return router
