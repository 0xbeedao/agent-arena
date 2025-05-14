"""
Generic model service for the Agent Arena application.
Provides a reusable service for CRUD operations on any model that inherits from DbBase.
"""

import sqlite3
from datetime import datetime
import uuid  # Added for generating IDs
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

from pydantic import BaseModel
from pydantic import Field

from agentarena.factories.logger_factory import LoggingService
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
        table_name: str,
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
        self.table_name = table_name
        self.table = db_service.db[table_name]
        self.model_name = model_class.__name__
        self.log = logging.get_logger(
            f"{self.model_name}service",
            model=self.model_name,
        )

    def parse_model(self, input_data: BaseModel) -> Tuple[Optional[T], ModelResponse]:
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
            if hasattr(e, "errors") and callable(e.errors):
                try:
                    error_detail = e.errors()
                except Exception:
                    pass  # Stick to str(e) if .errors() fails

            validation_resp = ValidationResponse(
                success=False,
                message="Input data could not be validated for the model.",
                data=error_detail,
            )
            return None, ModelResponse(success=False, validation=validation_resp)

    async def create(self, input_data: BaseModel) -> Tuple[Optional[T], ModelResponse]:
        """
        Create a new model instance.

        Args:
            input_data: The model data, expected to be compatible with self.model_class

        Returns:
            the created object or None
            the response detail
        """
        parsed_obj, problem = self.parse_model(input_data)
        if problem:
            return parsed_obj, problem

        # Now parsed_obj is a proper instance of self.model_class (e.g., AgentDTO)
        db_obj: T = parsed_obj.model_copy(deep=True)

        isonow = int(datetime.now().timestamp())
        # For new objects, created_at and updated_at are typically the same.
        db_obj.created_at = isonow
        db_obj.updated_at = isonow

        # This validateDTO is from DbBase, for business logic validation after Pydantic's parsing
        validation = self.db_service.validateDTO(db_obj)
        if not validation.success:
            self.log.error(
                f"Post-parsing DTO validation failed: {validation.message}",
                data=validation.data,
            )
            return None, ModelResponse(
                success=False, data=db_obj.model_dump(), validation=validation
            )

        try:
            self.table.insert(
                db_obj.model_dump(),  # Use the fully processed db_obj
                pk="id",
                foreign_keys=db_obj.get_foreign_keys(),  # Use db_obj here
                alter=not self.db_service.prod,
            )
        except sqlite3.IntegrityError as e:
            self.log.error(
                f"Integrity error while inserting {self.model_name} {db_obj.id}: {e}",
                exc_info=True,
            )
            invalidation = ValidationResponse(
                success=False,
                data=db_obj.model_dump(),
                message=f"Database integrity error: {e}",
            )
            return None, ModelResponse(success=False, validation=invalidation)

        self.log.info(f"Added {self.model_name} {db_obj.id}")
        self.db_service.add_audit_log(f"Added {self.model_name}: {db_obj.id}")
        return db_obj, ModelResponse(success=True, id=db_obj.id, validation=validation)

    async def create_many(
        self, obj_list: List[T]
    ) -> Tuple[List[T], List[ModelResponse]]:
        """
        Create multiple model instances.

        Args:
            obj_list: The list of model instances to create

        Returns:
            Two lists: the IDs of the created instances and a list of ModelResponse objects for errors
        """
        responses: List[str] = []
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
                if not response.success:
                    log.error(f"Failed to create", error=response.error)
                    problems.append(
                        ModelResponse(success=False, data=obj, error=response.error)
                    )
                else:
                    responses.append(created)
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
        row = self.table.get(str(obj_id))
        try:
            boundlog.debug("validating model")
            obj = self.model_class.model_validate(row) if row is not None else None
        except Exception as e:
            boundlog.error("error when loading", e)
            obj = None
        if obj is None:
            boundlog.warn(f"Not found")
            return None, ModelResponse(
                success=False,
                id=obj_id,
                error=f"{model_name} with ID {obj_id} not found",
            )
        return obj, ModelResponse(success=True, id=obj_id)

    async def update(self, obj: T) -> Tuple[T, ModelResponse]:
        """
        Update a model instance.

        Args:
            obj: The updated instance data, must have an id

        Returns:
            modelresponse object
        """
        if not obj.id:
            self.log.warn(f"Invalid object to update, no ID: {obj}")
            return obj, ModelResponse(success=False, data=obj, error="invalid object")

        boundlog = self.log.bind(obj_id=obj.id)
        validation = self.db_service.validateDTO(obj)
        if not validation.success:
            boundlog.error(f"Validation failed: {validation.data}")
            return obj, ModelResponse(success=False, data=obj, validation=validation)

        # Check if the object exists to update
        existing, response = await self.get(obj.id)
        if not response.success:
            return obj, ModelResponse(success=False, data=obj, error=response.error)

        # sanity checks done, now we can update
        updated = obj.model_dump(exclude=["id", "created_at"])
        existingObj = existing.model_dump(exclude=["updated_at"])
        cleaned = {}

        updates = {}
        # iterate and add only updates
        for key in updated:
            if key not in existingObj or existingObj[key] != updated[key]:
                cleaned[key] = updated[key]
                updates[key] = updated[key]

        cleaned["id"] = obj.id
        cleaned["updated_at"] = int(datetime.now().timestamp())

        try:
            self.table.update(obj.id, cleaned)
        except sqlite3.IntegrityError:
            boundlog.error(f"Integrity error while updating", obj=cleaned)
            invalidation = ValidationResponse(success=False, message="Integrity error")
            return obj, ModelResponse(success=False, id=obj.id, validation=invalidation)

        self.db_service.add_audit_log(f"Updated {self.model_name}, {obj.id}")

        return await self.get(obj.id)

    async def delete(self, obj_id: str) -> ModelResponse:
        """
        Delete a model instance.

        Args:
            obj_id: The ID of the instance to delete

        Returns:
            True if the instance was deleted, False if not found
        """
        existing = await self.get(obj_id)
        if existing is None:
            self.log.warn(f"No such id {obj_id}")
            return ModelResponse(
                success=False,
                id=obj_id,
                error=f"{self.model_name} with ID {obj_id} not found",
            )

        self.table.update(
            obj_id, {"deleted_at": int(datetime.now().timestamp()), "active": False}
        )
        self.log.info(f"Deleted {obj_id}")
        self.db_service.add_audit_log(f"Deleted {self.model_name}: {obj_id}")
        return ModelResponse(success=True, id=obj_id, data=existing)

    async def get_by_ids(
        self, obj_ids: List[str]
    ) -> Tuple[List[T], List[ModelResponse]]:
        """
        Get multiple model instances by their IDs.

        Args:
            obj_ids: The list of IDs to get

        Returns:
            A list of model instances and a list of ModelResponse objects for errors
        """
        responses = []
        problems = []
        for obj_id in obj_ids:
            obj, response = await self.get(obj_id)
            if not response.success:
                self.log.error(f"Failed to get: {response.error}")
                problems.append(response)
            else:
                responses.append(obj)
        return responses, problems

    def count_where(self, where: str, params: Dict, **kwargs) -> List[T]:
        """
        Count model instances by a WHERE clause.

        Args:
            where: The WHERE clause
            params: The parameters for the WHERE clause

        Returns:
            count
        """
        return self.table.count_where(where, params, **kwargs)

    async def get_where(self, where: str, params: Dict, **kwargs) -> List[T]:
        """
        Get model instances by a WHERE clause.

        Args:
            where: The WHERE clause
            params: The parameters for the WHERE clause

        Returns:
            A list of model instances
        """
        rows = self.table.rows_where(where, params, **kwargs)
        return [self.model_class.model_validate(row) for row in rows]

    async def list(self) -> List[T]:
        """
        List all model instances.

        Returns:
            A list of all model instances
        """
        rows = self.table.rows_where("active = ?", [True])
        return [self.model_class.model_validate(row) for row in rows]

    async def list_all(self) -> List[T]:
        """
        List all model instances, including inactive ones.

        Returns:
            A list of all model instances
        """
        return [self.model_class.model_validate(row) for row in self.table.rows]

    async def validate_list(self, obj_list: List[T]) -> List[ModelResponse]:
        if not obj_list:
            return []
        return await self.db_service.validate_list(obj_list)
