import os.path
from datetime import datetime

import structlog
from sqlite_utils.db import Database
from ulid import ULID


class DbService:

    def __init__(self, projectroot: str, dbfile: str, get_database):

        filename = dbfile.replace("<projectroot>", str(projectroot))
        self.log = structlog.getLogger("dbservice").bind(
            module="dbservice", db=os.path.basename(filename)
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
