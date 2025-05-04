import os.path
from typing import Any
from typing import Tuple

import structlog
from litequeue import LiteQueue

from agentarena.models.job import Job


class QueueService:
    """
    Provides Queue services, and a handle to the queue itself.
    """

    def __init__(self, projectroot: str, dbfile: str, get_queue):
        filename = dbfile.replace("<projectroot>", str(projectroot))
        self.log = structlog.getLogger(
            "queueservice", module="queue_service", db=os.path.basename(filename)
        )

        self.log.info("Setting up Job DB at %s", filename)
        self.q: LiteQueue = get_queue(filename)
        self.q.prune()

    def done(self, task):
        if task is None:
            return None

        job_id = "none"
        if task.data is not None and hasattr(task.data, "id"):
            job_id = task.data["id"]
        self.log.info(f"Task done: task# {task.message_id} job# {job_id}")
        return self.q.done(task.message_id)

    def drain(self):
        """
        Clear the queue
        """
        self.log.warn("Draining the queue")
        task = self.q.pop()
        while task is not None:
            self.done(task)
            task = self.q.pop()

    def get_job(self) -> Tuple[Job, Any]:
        if self.q.qsize() == 0:
            return None, None
        else:
            task = self.q.pop()
            if task is None:
                return None, None
            return Job.model_validate_json(task.data), task

    def send_job(self, job: Job):
        job.fill_defaults()
        self.q.put(job.model_dump_json())
