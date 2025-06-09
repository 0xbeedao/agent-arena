"""
Generic model service for the Agent Arena application.
Provides a reusable service for CRUD operations on any model that inherits from DbBase.
"""

import json
from datetime import datetime
from typing import Generic
from typing import List
from typing import Optional
from typing import Tuple
from typing import Type
from typing import TypeVar

from pydantic import BaseModel
from sqlmodel import Field
from sqlmodel import Session
from sqlmodel import SQLModel
from sqlmodel import select

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.dbbase import DbBase
from agentarena.models.validation import ModelResponse, ValidationResponse

from .db_service import DbService


T = TypeVar("T", bound=DbBase)  # SQLModel with a table
MC = TypeVar("MC", bound=SQLModel)  # model create


class ModelService(Generic[T, MC]):
    """
    Generic service for model operations.

    This service provides CRUD operations for any model that inherits from DbBase.
    It can be used directly or as a base class for more specialized services.
    """

    def __init__(
        self,
        model_class: Type[T],
        db_service: DbService,
        message_broker: MessageBroker,
        uuid_service: UUIDService = Field(description="UUID Service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):
        """
        Initialize the model service.

        Args:
            model_class: The Pydantic model class (must be a subclass of DbBase)
            db_service: The database service
            uuid_service: The UUID service
            logging: logging service
        """
        # Allow both DbBase and regular SQLModel classes
        if not (issubclass(model_class, DbBase) or issubclass(model_class, SQLModel)):
            raise TypeError(
                f"model_class must be a subclass of DbBase or SQLModel, got {model_class}"
            )

        self.model_class = model_class
        self.db_service = db_service
        self.message_broker = message_broker
        self.model_name = model_class.__name__.lower()
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
                data=(
                    error_detail.model_dump_json()
                    if isinstance(error_detail, BaseModel)
                    else json.dumps(error_detail)
                ),
            )
            return None, ModelResponse(success=False, validation=validation_resp)

    async def create(
        self, input_data: SQLModel, session: Session
    ) -> Tuple[Optional[T], ModelResponse]:
        """
        Create a new model instance.

        Args:
            input_data: The model data, expected to be the "create" model
            session: The DB Sesion

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
        if parsed_obj.id is None or parsed_obj.id == "":
            parsed_obj.id = self.uuid_service.make_id()

        # This validateDTO is from DbBase, for business logic validation after Pydantic's parsing
        validation = self.db_service.validateDTO(parsed_obj)
        if not validation.success:
            self.log.error(
                f"Post-parsing DTO validation failed: {validation.message}",
                data=validation.data,
            )
            return None, ModelResponse(
                success=False, data=parsed_obj.model_dump_json(), validation=validation
            )

        created = self.db_service.create(parsed_obj, session)

        self.log.info(f"Added {self.model_name} {created.id}")
        await self.message_broker.publish_model_change(
            f"sys.arena.{self.model_name}.{created.id}.create", created.id
        )
        self.db_service.add_audit_log(f"Added {self.model_name}: {created.id}", session)
        return created, ModelResponse(
            success=True, id=created.id, validation=validation
        )

    async def create_many(
        self, obj_list: List[SQLModel], session: Session
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
            created, problem = await self.create(obj, session)
            if problem:
                log.error(f"Validation failed: {problem}")
                problems.append(problem)
            if created:
                responses.append(created)
            else:
                log.warn(f"Validation failed with no problem given")
                problems.append(ModelResponse(success=False))
        log.debug(
            f"Created {len(responses)} {self.model_name} objects with {len(problems)} problems"
        )
        return responses, problems

    async def get(
        self, obj_id: str, session: Session
    ) -> Tuple[Optional[T], ModelResponse]:
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
        self, obj_id: str, obj: SQLModel, session: Session
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
        db_obj = session.get(self.model_class, obj_id)
        if not db_obj:
            return None, ModelResponse(success=False, error="Not found")
        obj_data = obj.model_dump(exclude_unset=True)
        log.debug("Values to update", updates=obj_data)
        db_obj.sqlmodel_update(obj_data)
        session.add(db_obj)
        session.commit()
        session.refresh(db_obj)
        await self.message_broker.publish_model_change(
            f"arena.{self.model_name}.{obj_id}.update",
            obj_id,
            detail=json.dumps(obj_data),
        )
        return db_obj, ModelResponse(success=True)

    async def delete(self, obj_id: str, session: Session) -> ModelResponse:
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

        self.log.info(f"Deleted {obj_id}")
        self.db_service.add_audit_log(f"Deleted {self.model_name}: {obj_id}", session)
        await self.message_broker.publish_model_change(
            f"sys.arena.{self.model_name}.{obj_id}.delete", obj_id
        )
        return ModelResponse(success=True, id=obj_id)

    async def get_by_ids(self, obj_ids: List[str], session: Session) -> List[T]:
        """
        Get multiple model instances by their IDs.

        Args:
            obj_ids: The list of IDs to get

        Returns:
            A list of model instances
        """
        if not obj_ids:
            return []

        stmt = select(self.model_class).filter(self.model_class.id.in_(obj_ids))  # type: ignore
        objects = session.exec(stmt).all()
        return objects  # type: ignore

    def get_session(self, session: Optional[Session] = None):
        if session:
            return session
        return self.db_service.get_session()

    async def list(self, session: Session):
        """
        List all model instances.

        Returns:
            A list of all model instances
        """
        return session.exec(select(self.model_class)).all()
