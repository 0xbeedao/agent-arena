import os.path
from datetime import datetime

from sqlite_utils.db import Database
from ulid import ULID


class DbService:
    """
    Provides db service, and a handle to the DB itself.
    """

    def __init__(self, projectroot: str, dbfile: str, get_database=None, logging=None):

        filename = dbfile.replace("<projectroot>", str(projectroot))
        self.log = logging.make_logger(
            "dbservice", module="dbservice", db=os.path.basename(filename)
        )
        self.log.info("Setting up DB at %s", filename)
        self.db: Database = get_database(filename)
        self.db.ensure_autocommit_off()
        self.db.execute("PRAGMA foreign_keys=ON")

    def add_audit_log(self, message):
        auditTable = self.db["audit"]
        self.log.info("Audit message: %s", message)
        auditTable.insert(
            {"id": ULID().hex, "timestamp": datetime.now(), "message": message}
        )
