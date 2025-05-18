import os.path
from datetime import datetime
from typing import List, Sequence

from pydantic import Field
from sqlite_utils.db import Database

from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.dbbase import DbBase
from agentarena.models.validation import ValidationResponse
from agentarena.core.services.uuid_service import UUIDService


class DbService:
    """
    Provides db service, and a handle to the DB itself.
    """

    def __init__(
        self,
        projectroot: str,
        dbfile: str,
        get_database=None,
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

        self.db: Database = get_database(filename)
        self.db.ensure_autocommit_off()
        self.db.execute("PRAGMA foreign_keys=ON")
        self.prod = prod
        self.uuid_service = uuid_service

    def add_audit_log(self, message):
        auditTable = self.db["audit"]
        self.log.info(message)
        auditTable.insert(
            {
                "id": self.uuid_service.make_id(),
                "timestamp": int(datetime.now().timestamp()),
                "message": message,
            }
        )

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
