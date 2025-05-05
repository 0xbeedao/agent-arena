"""
Generic model service for the Agent Arena application.
Provides a reusable service for CRUD operations on any model that inherits from DbBase.
"""

import json
import sqlite3
from datetime import datetime
from typing import Any
from typing import Dict
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

from pydantic import BaseModel
from ulid import ULID

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
        dbService: DbService,
        table_name: str,
        logging=None,
    ):
        """
        Initialize the model service.

        Args:
            model_class: The Pydantic model class (must be a subclass of DbBase)
            dbService: The database service
            table_name: Optional table name (if not provided, will be inferred from model_class name)
        """
        if not issubclass(model_class, DbBase):
            raise TypeError(
                f"model_class must be a subclass of DbBase, got {model_class}"
            )

        self.model_class = model_class
        self.dbService = dbService
        self.table_name = table_name
        self.table = dbService.db[table_name]
        self.model_name = model_class.__name__
        self.log = logging.get_logger(
            f"{self.model_name}service",
            module=f"{self.model_name}service",
            model=self.model_name,
        )

    async def create(self, obj: T) -> Tuple[str, ModelResponse]:
        """
        Create a new model instance.

        Args:
            obj: The model instance to create

        Returns:
            The ID of the created instance
        """
        db_obj = obj.model_copy()
        # Always make a new ID
        db_obj.id = ULID().hex
        # And set the timestamps
        isonow = datetime.now()
        db_obj.created_at = isonow
        db_obj.updated_at = isonow

        obj_id = str(db_obj.id)

        validation = obj.validateDTO()
        if not validation.success:
            self.log.error(f"Validation failed: %s", validation.data)
            return "", ModelResponse(success=False, data=obj, validation=validation)
        try:
            # TODO: turn off alter=true for production
            self.table.insert(
                db_obj.model_dump(),
                pk="id",
                foreign_keys=obj.get_foreign_keys(),
                alter=True,
            )
        except sqlite3.IntegrityError as e:
            self.log.error(f"Integrity error while inserting: %s", e)
            invalidation = ValidationResponse(
                success=False, data=obj, message="Integrity error"
            )
            return "", ModelResponse(success=False, validation=invalidation)
        self.log.info(f"Added #{obj_id}")
        self.dbService.add_audit_log(f"Added {self.model_name}: {obj_id}")
        return obj_id, ModelResponse(success=True, id=obj_id, validation=validation)

    async def create_many(
        self, obj_list: List[T]
    ) -> Tuple[List[str], List[ModelResponse]]:
        """
        Create multiple model instances.

        Args:
            obj_list: The list of model instances to create

        Returns:
            Two lists: the IDs of the created instances and a list of ModelResponse objects for errors
        """
        responses: List[str] = []
        problems: List[ModelResponse] = []
        for obj in obj_list:
            validation = obj.validateDTO()
            if not validation.success:
                self.log.error(f"Validation failed: %s", validation.data)
                problems.append(
                    ModelResponse(success=False, data=obj, validation=validation)
                )
            else:
                [id, response] = await self.create(obj)
                if not response.success:
                    self.log.error(f"Failed to create: %s", response.error)
                    problems.append(
                        ModelResponse(success=False, data=obj, error=response.error)
                    )
                else:
                    responses.append(id)
                    self.log.info(f"Created: %s", id)

        return responses, problems

    async def get(self, obj_id: str) -> Tuple[Optional[T], ModelResponse]:
        """
        Get a model instance by ID.

        Args:
            obj_id: The ID of the instance to get

        Returns:
            The model instance, or None if not found
        """
        model_name = self.model_class.__name__
        boundlog = self.log.bind(get=obj_id)
        boundlog.info("Getting from DB")
        row = self.table.get(str(obj_id))
        try:
            boundlog.debug("validating model")
            obj = self.model_class.model_validate(row) if row is not None else None
        except Exception as e:
            self.log.error("error when loading", e)
            obj = None
        if obj is None:
            self.log.warn(f"Not found #%s", obj_id)
            return None, ModelResponse(
                success=False,
                id=obj_id,
                error=f"{model_name} with ID {obj_id} not found",
            )
        return obj, ModelResponse(success=True, id=obj_id)

    async def update(self, obj_id: str, obj: T) -> ModelResponse:
        """
        Update a model instance.

        Args:
            obj_id: The ID of the instance to update
            obj: The updated instance data

        Returns:
            True if the instance was updated, False if not found
        """
        validation = obj.validateDTO()
        if not validation.success:
            self.log.error(f"Validation failed: %s", validation.data)
            return ModelResponse(success=False, data=obj, validation=validation)

        # Check if the object exists to update
        [existing, response] = await self.get(obj_id)
        if not response.success:
            return ModelResponse(success=False, id=obj_id, error=response.error)

        # sanity checks done, now we can update
        model_name = self.model_class.__name__
        updated = obj.model_dump(exclude=["id", "created_at"])
        existingObj = existing.model_dump(exclude=["updated_at"])
        cleaned = {}

        updates = {}
        # iterate and add only updates
        for key in updated:
            if existingObj[key] != updated[key]:
                cleaned[key] = updated[key]
                updates[key] = updated[key]

        cleaned["updated_at"] = datetime.now()

        try:
            self.table.update(obj_id, cleaned)
        except sqlite3.IntegrityError:
            self.log.error(f"Integrity error while updating: %s", cleaned)
            invalidation = ValidationResponse(success=False, message="Integrity error")
            return ModelResponse(success=False, id=obj_id, validation=invalidation)

        self.dbService.add_audit_log(
            f"Updated {self.model_name}, #{obj_id} with {json.dumps(updates)}"
        )
        return ModelResponse(success=True, id=obj_id, data=cleaned)

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
            self.log.warn(f"No such id #%s", obj_id)
            return ModelResponse(
                success=False,
                id=obj_id,
                error=f"{self.model_name} with ID {obj_id} not found",
            )

        self.table.update(obj_id, {"deleted_at": datetime.now(), "active": False})
        self.log.info(f"Deleted #%s", obj_id)
        self.dbService.add_audit_log(f"Deleted {self.model_name}: {obj_id}")
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
            [obj, response] = await self.get(obj_id)
            if not response.success:
                self.log.error(f"Failed to get: %s", response.error)
                problems.append(response)
            else:
                responses.append(obj)
        return responses, problems

    async def get_where(self, where: str, params: Dict) -> List[T]:
        """
        Get model instances by a WHERE clause.

        Args:
            where: The WHERE clause
            params: The parameters for the WHERE clause

        Returns:
            A list of model instances
        """
        rows = self.table.rows_where(where, params)
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
