import os.path
from typing import Any
from typing import Tuple

from litequeue import LiteQueue

from agentarena.models.job import JsonRequestJob
from agentarena.services.model_service import ModelService


class QueueService:
    """
    Provides Queue services, and a handle to the queue itself.
    """

    def __init__(
        self,
        projectroot: str,
        dbfile: str,
        get_queue=None,
        job_service: ModelService[JsonRequestJob] = None,
        logging=None,
    ):
        filename = dbfile.replace("<projectroot>", str(projectroot))
        self.log = logging.get_logger(
            "queueservice", module="queue_service", db=os.path.basename(filename)
        )
        self.job_service = job_service
        self.log.info("Setting up Job DB at %s", filename)
        self.q: LiteQueue = get_queue(filename)
        self.q.prune()

    def done(self, task, job, status="completed"):
        if task is None:
            return None

        job_id = job.id
        self.log.info(f"Task {status}: task# {task.message_id} job# {job_id}")
        job.status = status
        self.job_service.update(job)
        return self.q.done(task.message_id)

    def drain(self):
        """
        Clear the queue
        """
        self.log.warn("Draining the queue")
        job, task = self.get_job()
        while task is not None:
            self.done(task, job)
            job, task = self.get_job()

    def get_job(self) -> Tuple[JsonRequestJob, Any]:
        if self.q.qsize() == 0:
            return None, None
        else:
            task = self.q.pop()
            if task is None:
                return None, None
            return JsonRequestJob.model_validate_json(task.data), task

    def requeue_job(self, job: JsonRequestJob, task):
        self.q.done(task.message_id, status="waiting")
        self.send_job(job)

    def send_job(self, job: JsonRequestJob):
        if not job.id:
            job.fill_defaults()
            job.attempt = 1
            _, response = self.job_service.create(job)
        else:
            job.attempt += 1
            response = self.job_service.update(job)

        if not response.success:
            self.log.warn("Could not persist job: {job}")

        self.q.put(job.model_dump_json())
