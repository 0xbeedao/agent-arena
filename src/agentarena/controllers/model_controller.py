from typing import Dict
from typing import Generic
from typing import List
from typing import TypeVar

from fastapi import APIRouter
from fastapi import HTTPException
from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
from agentarena.models.dbbase import DbBase
from agentarena.services.model_service import ModelService

T = TypeVar("T", bound=DbBase)


class ModelController(Generic[T]):
    def __init__(
        self,
        model_name: str = Field("The model name"),
        model_service: ModelService[T] = Field(
            description="The model service for this model"
        ),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """
        Initialize the model controller.

        Args:
            model_name: Name of model
            db_service: The database service
            table_name: Optional table name (if not provided, will be inferred from model_class name)
        """
        self.model_name = model_name
        self.model_service = model_service
        self.log = logging.get_logger(
            f"{model_name}_controller",
            module=f"{model_name}_controller",
            model=model_name,
        )

    async def create_model(
        self, req: T = Field(description="The model create request")
    ) -> T:
        """
        Create a new instance of the model.

        Args:
            Model DTO Object

        Returns:
            new model object

        Raises:
            HttpException for validation errors
        """
        obj, response = await self.model_service.create(req)
        if not response.success:
            raise HTTPException(status_code=422, detail=response.validation)
        return obj

    async def get_model(
        self, obj_id: str = Field(description="The id of the object")
    ) -> T:
        """
        Get an instance of the model by id

        Args:
            obj_id - the object to get

        Returns:
            instance of this model

        Raises:
            HttpException if not found or invalid
        """
        obj, response = await self.model_service.get(obj_id)
        if not response.success:
            raise HTTPException(status_code=404, detail=response.error)
        return obj

    async def get_model_list(self) -> List[T]:
        """
        Get a list of all models.

        Returns:
            A list of feature configurations
        """
        return await self.model_service.list()

    async def update_model(
        self,
        req_id: str = Field(description="The id of the object to update"),
        req: T = Field(description="updated model"),
    ) -> T:
        """
        Update the model

        Args:
            req_id: The id of the object to update
            req: the new model config

        Returns:
            the updated object

        Raises:
            HTTPException: If the object is not found
        """

        to_update = req.model_copy()
        to_update.id = req_id
        obj, response = await self.model_service.update(to_update)
        if not response.success:
            self.log.info(
                "Failed to update object: %s", response.validation.model_dump_json()
            )
            raise HTTPException(status_code=422, detail=response.validation)
        return obj

    async def delete_model(
        self,
        obj_id: str,
    ) -> Dict[str, bool]:
        """
        Delete a model instance

        Args:
            obj_id: The ID of the object to delete

        Returns:
            A dictionary indicating success

        Raises:
            HTTPException: If the feature is not found
        """
        response = await self.model_service.delete(obj_id)
        if not response.success:
            raise HTTPException(status_code=422, detail=response.validation)
        return {"success": response.success}

    def get_router(self, base="/api"):
        router = APIRouter(prefix=f"{base}/{self.model_name}", tags=[self.model_name])

        @router.post("/", response_model=T)
        async def create(req: T):
            return await self.create_model(req)

        @router.get("/{obj_id}", response_model=T)
        async def get(obj_id: str):
            return await self.get_model(obj_id)

        @router.get("/", response_model=List[T])
        async def list_all():
            return await self.get_model_list()

        @router.get("/list", response_model=List[T])
        async def list_alias():
            return await self.get_model_list()

        @router.put("/", response_model=T)
        async def update(req_id: str, req: T):
            return await self.update_model(req_id, req)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            return await self.delete_model(obj_id)

        return router
