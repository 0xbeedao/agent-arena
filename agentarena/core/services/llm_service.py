from datetime import datetime

import llm
from sqlmodel import Field

from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import GenerateJob
from agentarena.models.job import GenerateJobCreate


class LLMService:

    def __init__(
        self,
        db_service: DbService,
        message_broker: MessageBroker = Field(),
        uuid_service: UUIDService = Field(),
        logging: LoggingService = Field(),
    ):
        self.log = logging.get_logger("llm")
        self.message_broker = message_broker
        self.db_service = db_service
        self.uuid_service = uuid_service

    def generate(self, model_alias: str, prompt: str) -> str:
        """
        Query the LLM and return the text
        """
        try:
            model = llm.get_model(model_alias)
            return model.prompt(prompt).text()
        except llm.UnknownModelError as ue:
            self.log.warn("Could not get model from LLM", model=model_alias)
            raise ue

    def make_generate_job(
        self, job_id: str, model: str, prompt: str
    ) -> GenerateJobCreate:
        """
        Make a job for the generation, and save its output to db.
        """
        job = GenerateJobCreate(
            job_id=job_id,
            model=model,
            prompt=prompt,
            state=JobState.IDLE,
            started_at=0,
            text=None,
        )
        return job

    def execute_job(self, gen_id: str):
        log = self.log.bind(gen_id=gen_id)
        job = None
        generated = ""
        model = ""
        prompt = ""

        with self.db_service.get_session() as session:
            job = session.get(GenerateJob, gen_id)
            if not job:
                log.warn(f"Invalid GenerateJob")
                return None

            job.started_at = int(datetime.now().timestamp())
            job.state = JobState.REQUEST
            model = job.model
            prompt = job.prompt
            session.commit()

        log.debug("start generation")
        try:
            generated = self.generate(model, prompt)
        except llm.UnknownModelError:
            log.error(f"Invalid model {model}")
            with self.db_service.get_session() as session:
                job = session.get(GenerateJob, gen_id)
                if job:
                    job.state = JobState.FAIL
                    job.finished_at = int(datetime.now().timestamp())
                    session.commit()
        log.debug("end generation")

        with self.db_service.get_session() as session:
            job = session.get(GenerateJob, gen_id)
            if not job:
                log.warn(f"Invalid GenerateJob")
                return None

            job.state = JobState.COMPLETE
            job.generated = generated
            job.finished_at = int(datetime.now().timestamp())
            session.commit()

        return job
