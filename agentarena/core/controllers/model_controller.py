from typing import Dict
from typing import Generic
from typing import List
from typing import Type
from typing import TypeVar

from fastapi import APIRouter
from fastapi import Body
from fastapi import HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.models.dbbase import DbBase

T = TypeVar("T", bound=DbBase)
MC = TypeVar("MC", bound=SQLModel)  # model creation type, e.g. CommandJobCreate
MU = TypeVar("MU", bound=SQLModel)  # model update type, e.g. CommandJobUpdate
MP = TypeVar("MP", bound=BaseModel)  # model public type, e.g. CommandJobPublic


class ModelController(Generic[T, MC, MU, MP]):
    def __init__(
        self,
        base_path: str = "/api",
        model_name: str = Field("The model name"),
        model_create: Type[MC] = Field(description="The create model"),
        model_update: Type[MU] = Field(description="The update model"),
        model_public: Type[MP] = Field(description="The public model"),
        model_service: ModelService[T, MC] = Field(
            description="The model service for this model"
        ),
        template_service: JinjaRenderer = Field(description="The template service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """
        Initialize the model controller.

        Args:
            model_name: Name of model
            db_service: The database service
            table_name: Optional table name (if not provided, will be inferred from model_class name)
        """
        safe_path = base_path.rstrip("/")
        if len(safe_path.split("/")) == 2 and not safe_path.endswith(model_name):
            safe_path = f"{safe_path}/{model_name}"
        self.base_path = safe_path.lower()
        self.model_name = model_name
        self.model_create = model_create
        self.model_update = model_update
        self.model_public = model_public
        self.model_service = model_service
        self.template_service = template_service
        self.log = logging.get_logger(
            "controller", model=model_name, path=self.base_path
        )

    async def create_model(self, req: MC, session: Session) -> T:
        """
        Create a new instance of the model.

        Args:
            Model DTO Object

        Returns:
            new model object

        Raises:
            HttpException for validation errors
        """
        self.log.info("create request", req=req)
        obj, response = await self.model_service.create(req, session)
        if response and not response.success:
            raise HTTPException(status_code=422, detail=response.model_dump())
        if not obj:
            raise HTTPException(status_code=500, detail="internal error")
        return obj

    def convert_to_public(self, obj: DbBase) -> MP:
        """
        Convert the model to a public model
        """
        if hasattr(obj, "get_public"):
            self.log.debug("converting to public", obj=obj.id)
            return obj.get_public()  # type: ignore
        self.log.debug("no get_public method", obj=obj.id)
        return self.model_public.model_validate(obj)

    async def get_model(self, obj_id: str, session: Session) -> MP:
        """
        Get an instance of the model by id

        Args:
            obj_id - the object to get

        Returns:
            instance of this model

        Raises:
            HttpException if not found or invalid
        """
        obj, response = await self.model_service.get(obj_id, session)
        if not response.success:
            raise HTTPException(status_code=404, detail=response.model_dump())
        if not obj:
            raise HTTPException(status_code=500, detail="internal error")
        pub = self.convert_to_public(obj)
        return pub

    async def get_model_with_format(
        self, obj_id: str, session: Session, format: str = "md"
    ) -> Response:
        """
        Get an instance of the model by id with a specific format
        """
        obj, response = await self.model_service.get(obj_id, session)
        if not response.success or not obj:
            raise HTTPException(status_code=404, detail=response.model_dump())
        pub = self.convert_to_public(obj)
        if format == "md":
            try:
                self.log.info(
                    "rendering template", model=self.model_name, format=format, obj=pub
                )
                rendered = self.template_service.render_template(
                    f"{self.model_name}.{format}", {self.model_name: pub}
                )
                return Response(content=rendered, media_type="text/markdown")
            except Exception as e:
                self.log.error("Invalid template", error=e)
                raise HTTPException(status_code=422, detail="bad template")
        return Response(content=obj.model_dump_json(), media_type="application/json")

    async def get_model_list(self, session: Session) -> List[MP]:
        """
        Get a list of all models.

        Returns:
            A list of feature configurations
        """
        raw = await self.model_service.list(session)
        return [self.convert_to_public(obj) for obj in raw]

    async def update_model(self, req_id: str, req: MU, session: Session) -> MP:
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
        obj, response = await self.model_service.update(req_id, req, session)
        if not response.success:
            self.log.info("Failed to update object", validation=response)
            raise HTTPException(status_code=422, detail=response.model_dump())
        if not obj:
            raise HTTPException(status_code=500, detail="internal error")
        data = obj
        if hasattr(obj, "model_dump"):
            data = obj.model_dump()

        return self.model_public.model_validate(data)

    async def delete_model(self, obj_id: str, session: Session) -> Dict[str, bool]:
        """
        Delete a model instance

        Args:
            obj_id: The ID of the object to delete

        Returns:
            A dictionary indicating success

        Raises:
            HTTPException: If the feature is not found
        """
        response = await self.model_service.delete(obj_id, session)
        if not response.success:
            raise HTTPException(status_code=422, detail=response.model_dump())
        return {"success": response.success}

    def get_router(self):
        prefix = self.base_path
        self.log.info("setting up routes", path=prefix)

        router = APIRouter(prefix=prefix, tags=[self.model_name])

        # Use a factory function to properly create routes with correct types
        def create_endpoint():
            @router.post("/", response_model=MP)
            async def create(req: MC = Body(...)):
                with self.model_service.get_session() as session:
                    return await self.create_model(req, session)

            # Manually set the annotation to the concrete type
            create.__annotations__["req"] = self.model_create
            return create

        def update_endpoint():
            @router.patch("/", response_model=MP)
            async def update(req_id: str, req: MU = Body(...)):
                with self.model_service.get_session() as session:
                    return await self.update_model(req_id, req, session)

            # Manually set the annotation to the concrete type
            update.__annotations__["req"] = self.model_update
            return update

        # Create the endpoints
        create_endpoint()
        update_endpoint()

        @router.get("/{obj_id}.{format}", response_model=str)
        async def get_md(obj_id: str, format: str = "md"):
            with self.model_service.get_session() as session:
                return await self.get_model_with_format(obj_id, session, format=format)

        @router.get("/{obj_id}", response_model=MP)
        async def get(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.get_model(obj_id, session)

        @router.get("", response_model=List[MP])
        async def list_all():
            with self.model_service.get_session() as session:
                return await self.get_model_list(session)

        @router.delete("/{obj_id}", response_model=Dict[str, bool])
        async def delete(obj_id: str):
            with self.model_service.get_session() as session:
                return await self.delete_model(obj_id, session)

        return router
