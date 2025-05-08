from datetime import datetime
import sqlite3
from typing import Optional

import sqlite_utils
from agentarena.models.job import JsonRequestJob
from agentarena.services.model_service import ModelService


class JobService:
    """
    Manages the Job queue
    """

    def __init__(
        self,
        requestjob_service: ModelService[JsonRequestJob] = None,
        logging=None,
    ):
        self.log = logging.get_logger("jobservice")
        self.model_service = requestjob_service

    async def done(self, job, status="completed") -> bool:
        self.log.info(f"status change", old=job.status, new=status)
        job.status = status
        response = await self.model_service.update(job.id, job)
        return response.success

    async def drain(self):
        """
        Clear the queue
        """
        self.log.warn("Draining the queue")
        job = await self.get_job()
        while job is not None:
            await self.done(job)
            job = await self.get_job()

    async def get(self) -> Optional[JsonRequestJob]:
        jobs: JsonRequestJob = await self.model_service.get_where(
            "status = :idle or status = :waiting and send_at <= :now",
            {
                "idle": "IDLE",
                "waiting": "WAITING",
                "now": int(datetime.now().timestamp()),
            },
            limit=1,
            order_by="created_at asc",
        )
        if len(jobs) > 0:
            return jobs[0]
        return None

    async def resend(self, job: JsonRequestJob, at=Optional[int]):
        job.attempt += 1
        job.send_at = at if at is not None else int(datetime.now().timestamp())
        self.log.info("rescheduling", job=job.id, to=job.send_at)
        response = await self.model_service.update(job.id, job)
        return job.id, response

    async def send(self, job: JsonRequestJob):
        job_id = job.id

        if not job_id:
            job.attempt = 1
            job_id, response = await self.model_service.create(job)
        else:
            job.attempt += 1
            response = await self.model_service.update(job.id, job)

        return job_id, response

    async def size(self) -> int:
        """
        return queue size
        """
        ct = 0
        try:
            ct = self.model_service.table.count_where(
                "status = :idle or status = :waiting",
                {"idle": "IDLE", "waiting": "WAITING"},
            )
        except sqlite3.OperationalError:
            self.log.warn("no table, possibly empty queue")
        except sqlite_utils.db.NotFoundError:
            self.log.warn("no db? possibly empty?")
        return ct
