import os.path
from datetime import datetime
from typing import Callable
from typing import List
from typing import Sequence

from pydantic import Field
from sqlmodel import Session
from sqlmodel import SQLModel

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.audit import AuditMessage
from agentarena.models.dbbase import DbBase
from agentarena.models.validation import ValidationResponse


class DbService:
    """
    Provides db service, and a handle to the DB itself.
    """

    def __init__(
        self,
        projectroot: str,
        dbfile: str,
        get_engine: Callable,
        memory=False,
        prod=False,
        uuid_service: UUIDService = Field(description="UUID Service"),
        logging: LoggingService = Field(description="Logger factory"),
    ):

        if memory:
            filename = ":memory:"
            self.log = logging.get_logger("service", db="memory")
            self.log.info("setting up memory db")
        else:
            filename = dbfile.replace("<projectroot>", str(projectroot))
            self.log = logging.get_logger("service", db=os.path.basename(filename))
            self.log.info("Setting up DB")

        self.engine = get_engine(filename)
        self.prod = prod
        self.uuid_service = uuid_service
        self._created = False

    def create_db(self):
        if not self._created:
            self.log.info("Creating DB")
            SQLModel.metadata.create_all(self.engine)
            self._created = True
        return self

    def add_audit_log(self, message, session: Session):
        audit = self.create(
            AuditMessage(
                id=self.uuid_service.make_id(),
                created_at=int(datetime.now().timestamp()),
                message=message,
            ),
            session,
        )
        self.log.info("audit", audit=audit)

    def create(self, obj, session: Session):
        session.add(obj)
        session.commit()
        session.refresh(obj)
        return obj

    def get_session(self):
        return Session(self.engine)

    def fill_defaults(self, obj: DbBase):
        obj_id = self.uuid_service.ensure_id(obj)
        obj.id = obj_id
        c = getattr(obj, "created_at", None)
        if c is None or c == 0 or c == "":
            obj.created_at = int(datetime.now().timestamp())
        return obj

    def validateDTO(self, obj: DbBase) -> ValidationResponse:
        """
        Validate the model.

        Returns:
            ValidationResponse: The validation response.
        """
        self.fill_defaults(obj)
        return obj.validateDTO()

    async def validate_list(
        self, obj_list: Sequence[DbBase]
    ) -> List[ValidationResponse]:
        """
        Validate a list of models.

        Args:
            obj_list: The list of models to validate.

        Returns:
            ValidationResponse: The validation response for errors.
        """
        messages = []
        for obj in obj_list:
            validation = self.validateDTO(obj)
            if not validation.success:
                messages.extend(validation)

        return messages
