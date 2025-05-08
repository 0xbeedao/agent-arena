from datetime import datetime
from agentarena.models.job import JobState, JsonRequestJob
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService


FINAL_STATES = [JobState.WAITING.value, JobState.FAIL.value, JobState.COMPLETE.value]
ALL_STATES = [state.value for state in JobState]


class QueueService:
    """
    Provides DB backed job queue services
    """

    def __init__(
        self,
        db_service: DbService = None,
        job_service: ModelService[JsonRequestJob] = None,
        logging=None,
    ):
        self.db_service = db_service
        self.job_service = job_service
        self.log = logging.get_logger(module="jobqueue_service")

    async def drain(self, message=""):
        log = self.log.bind(method="drain")
        log.info("Draining queue")
        job = await self.get_next()
        while job is not None:
            self.update_state(job.id, "complete", message=message)
        log.info("drain complete")

    async def send_job(self, job: JsonRequestJob):
        if job.id is None:
            job.attempt = 1
            job.started_at = 0
            job.finished_at = 0
        created, response = await self.job_service.create(job)
        if response.success:
            return created
        return None

    async def get_next(self) -> JsonRequestJob:
        next = await self.job_service.get_where(
            "state = :idle and send_at < :now",
            {"idle": JobState.IDLE.value, "now": int(datetime.now().timestamp())},
            order_by="priority asc, created_at asc",
            limit=1,
        )
        self.log.info(f"next: {next}")
        if next is None or len(next) == 0:
            return None
        job = next[0]
        job.started_at = int(datetime.now().timestamp())
        job.state = JobState.REQUEST.value
        startedJob, response = await self.job_service.update(job)
        if response.success:
            return startedJob
        return None

    async def update_state(
        self, job_id: str, state: str, message: str = ""
    ) -> JsonRequestJob:

        if not state in ALL_STATES:
            log.warn(f"Invalid state: {state}")
            return False

        log = self.log.bind(method="update_state", state=state, job_id=job_id)

        job, response = await self.job_service.get(job_id)

        if job is None or not response.success:
            log.warn("No such job")
            return None

        log = log.bind(attempt=job.attempt)
        job.state = state
        sent = None
        if state in FINAL_STATES:
            log.info("final state for job")
            job.finished_at = int(datetime.now().timestamp())
            job.final_message = message
            _, response = await self.job_service.update(job)

            if response.success:
                again = job.make_attempt()
                self.log.info("Requeue request for the new job")
                sent = await self.send_job(again)
                self.log.debug(f"Requeued: {sent}")
            else:
                log.info("Couldn't update the old job, so didn't make a new one")
        else:
            log.info("job state updated to a non-final state, saving")
            job.finished_at = int(datetime.now().timestamp())
            sent, response = await self.job_service.update(job)
            if not response.success:
                sent = None
        return sent
