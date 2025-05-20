"""
Generic model service for the Agent Arena application.
Provides a reusable service for CRUD operations on any model that inherits from DbBase.
"""

from datetime import datetime
import json
from typing import Any
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

from fastapi import HTTPException
from pydantic import BaseModel
from pydantic import Field
from sqlmodel import SQLModel, select

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.dbbase import DbBase
from agentarena.models.validation import ValidationResponse

from .db_service import DbService


class ModelResponse(BaseModel):
    """
    Response model for creating a new instance.

    This model is used to return the ID of the created instance.
    """

    success: bool
    id: Optional[str] = None
    validation: Optional[ValidationResponse] = None
    error: Optional[str] = None
    data: Optional[Any] = None


T = TypeVar("T", bound=DbBase)


class ModelService(Generic[T]):
    """
    Generic service for model operations.

    This service provides CRUD operations for any model that inherits from DbBase.
    It can be used directly or as a base class for more specialized services.
    """

    def __init__(
        self,
        model_class: Type[T],
        db_service: DbService,
        uuid_service: UUIDService = Field(description="UUID Service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """
        Initialize the model service.

        Args:
            model_class: The Pydantic model class (must be a subclass of DbBase)
            db_service: The database service
            table_name: Optional table name (if not provided, will be inferred from model_class name)
        """
        if not issubclass(model_class, DbBase):
            raise TypeError(
                f"model_class must be a subclass of DbBase, got {model_class}"
            )

        self.model_class = model_class
        self.db_service = db_service
        self.model_name = model_class.__name__
        self.uuid_service = uuid_service
        self.log = logging.get_logger(
            "service",
            model=self.model_name,
        )

    def parse_model(
        self, input_data: BaseModel
    ) -> Tuple[Optional[T], Optional[ModelResponse]]:
        try:
            # Ensure input_data is converted/validated to the specific model type
            # self.model_class is Type[T] where T is bound to DbBase
            # model_validate can take a dict or another BaseModel instance
            parsed_obj = self.model_class.model_validate(input_data)
            return parsed_obj, None
        except Exception as e:  # Broad exception for Pydantic validation errors
            self.log.error(
                f"Validation failed during model parsing: {str(e)}",
                input_data=str(input_data)[:500],  # Log snippet of input data
                exc_info=True,
            )
            error_detail = str(e)
            # Try to get more structured errors from Pydantic's ValidationError
            if hasattr(e, "errors") and callable(e.errors):  # type: ignore
                try:
                    error_detail = e.errors()  # type: ignore
                except Exception:
                    pass  # Stick to str(e) if .errors() fails

            validation_resp = ValidationResponse(
                success=False,
                message="Input data could not be validated for the model.",
                data=error_detail,
            )
            return None, ModelResponse(success=False, validation=validation_resp)

    async def create(self, input_data: SQLModel) -> Tuple[Optional[T], ModelResponse]:
        """
        Create a new model instance.

        Args:
            input_data: The model data, expected to be the "create" model

        Returns:
            the created object or None
            the response detail
        """
        parsed_obj, problem = self.parse_model(input_data)
        if problem or parsed_obj is None:

            return parsed_obj, problem  # type: ignore

        # Now parsed_obj is a proper instance of self.model_class (e.g., AgentDTO)
        # db_obj: T = parsed_obj.model_copy(deep=True)

        isonow = int(datetime.now().timestamp())
        parsed_obj.created_at = isonow
        parsed_obj.updated_at = isonow
        parsed_obj.id = self.uuid_service.make_id()

        # This validateDTO is from DbBase, for business logic validation after Pydantic's parsing
        print(f"Now creating #{parsed_obj.id}")
        validation = self.db_service.validateDTO(parsed_obj)
        if not validation.success:
            self.log.error(
                f"Post-parsing DTO validation failed: {validation.message}",
                data=validation.data,
            )
            return None, ModelResponse(
                success=False, data=parsed_obj.model_dump(), validation=validation
            )

        self.db_service.create(parsed_obj)

        self.log.info(f"Added {self.model_name} {parsed_obj.id}")
        self.db_service.add_audit_log(f"Added {self.model_name}: {parsed_obj.id}")
        return parsed_obj, ModelResponse(
            success=True, id=parsed_obj.id, validation=validation
        )

    async def create_many(
        self, obj_list: List[T]
    ) -> Tuple[List[T], List[ModelResponse]]:
        """
        Create multiple model instances.

        Args:
            obj_list: The list of model instances to create

        Returns:
            Two lists: the created instances and a list of ModelResponse objects for errors
        """
        responses: List[T] = []
        problems: List[ModelResponse] = []
        log = self.log.bind(method="create_many")
        for obj in obj_list:
            validation = self.db_service.validateDTO(obj)
            if not validation.success:
                log.error(f"Validation failed: {validation.data}")
                problems.append(
                    ModelResponse(success=False, data=obj, validation=validation)
                )
            else:
                [created, response] = await self.create(obj)
                if response is not None and not response.success:
                    log.error(f"Failed to create", error=response.error)
                    problems.append(
                        ModelResponse(success=False, data=obj, error=response.error)
                    )
                elif created is None:
                    log.error(f"Failed to create - null response", error=None)
                    problems.append(ModelResponse(success=False, data=obj, error=None))
                else:
                    responses.append(created)  # type: ignore
                    log.info(f"Created", created=created.id)

        return responses, problems

    async def get(self, obj_id: str) -> Tuple[Optional[T], ModelResponse]:
        """
        Get a model instance by ID.

        Args:
            obj_id: The ID of the instance to get

        Returns:
            The model instance, or None if not found
        """
        if obj_id is None or obj_id == "":
            return None, ModelResponse(success=False, id=None, error="obj_id required")
        model_name = self.model_name
        boundlog = self.log.bind(obj_id=obj_id)
        boundlog.info("Getting from DB")
        with self.db_service.get_session() as session:
            obj = session.get(self.model_class, obj_id)

            if obj is None:
                boundlog.warn(f"Not found")
                return None, ModelResponse(
                    success=False,
                    id=obj_id,
                    error=f"{model_name} with ID {obj_id} not found",
                )

            return obj, ModelResponse(success=True, id=obj_id)

    async def update(
        self, obj_id: str, obj: SQLModel
    ) -> Tuple[Optional[T], ModelResponse]:
        """
        Patches the object safely and saves to DB
        """
        if not obj_id:
            return None, ModelResponse(success=False, error="No obj_id given")
        if self.model_class is None:
            return None, ModelResponse(success=False, error="No model_class")
        log = self.log.bind(id=obj_id)
        log.info("patching")
        with self.db_service.get_session() as session:
            db_obj = session.get(self.model_class, obj_id)
            if not db_obj:
                return None, ModelResponse(success=False, error="Not found")
            obj_data = obj.model_dump(exclude_unset=True)
            log.debug("Values to update", updates=obj_data)
            db_obj.sqlmodel_update(obj_data)
            session.add(db_obj)
            session.commit()
            session.refresh(db_obj)
            return db_obj, ModelResponse(success=True)

    async def delete(self, obj_id: str) -> ModelResponse:
        """
        Delete a model instance.

        Args:
            obj_id: The ID of the instance to delete

        Returns:
            True if the instance was deleted, False if not found
        """
        if obj_id is None:
            return ModelResponse(
                success=False,
                id=obj_id,
                error=f"{self.model_name} with ID {obj_id} not found",
            )
        with self.db_service.get_session() as session:

            existing = session.get(self.model_class, obj_id)

            if existing is None:
                self.log.warn(f"No such id {obj_id}")
                return ModelResponse(
                    success=False,
                    id=obj_id,
                    error=f"{self.model_name} with ID {obj_id} not found",
                )
            session.delete(existing)
            session.flush()
            session.refresh(existing)

            self.log.info(f"Deleted {obj_id}")
            self.db_service.add_audit_log(f"Deleted {self.model_name}: {obj_id}")
            return ModelResponse(success=True, id=obj_id, data=existing)

    async def get_by_ids(self, obj_ids: List[str]):
        """
        Get multiple model instances by their IDs.

        Args:
            obj_ids: The list of IDs to get

        Returns:
            A list of model instances
        """
        if not obj_ids:
            return []

        with self.db_service.get_session() as session:
            stmt = select(self.model_class).filter(self.model_class.id.in_(obj_ids))
            objects = session.exec(stmt)
            return objects

    async def list(self):
        """
        List all model instances.

        Returns:
            A list of all model instances
        """
        with self.db_service.get_session() as session:
            return session.exec(select(self.model_class))
