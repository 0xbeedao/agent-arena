from datetime import datetime
from sqlmodel import Field, Session

from agentarena.actors.models import Agent
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
import llm

from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.constants import JobState
from agentarena.models.job import GenerateJob


class LLMService:

    def __init__(
        self,
        message_broker: MessageBroker = Field(),
        uuid_service: UUIDService = Field(),
        logging: LoggingService = Field(),
    ):
        self.log = logging.get_logger("llm")
        self.message_broker = message_broker
        self.uuid_service = uuid_service

    def generate(self, agent: Agent, prompt: str) -> str:
        """
        Query the LLM and return the text
        """
        try:
            model = llm.get_model(agent.model)
            return model.prompt(prompt).text()
        except llm.UnknownModelError as ue:
            self.log.warn("Could not get model from LLM", model=agent.model)
            raise ue

    def add_generate_job(
        self, agent: Agent, prompt: str, session: Session
    ) -> GenerateJob:
        """
        Make a job for the generation, and save its output to db.
        """
        job = GenerateJob(
            id=self.uuid_service.make_id(),
            model=agent.model,
            prompt=prompt,
            state=JobState.REQUEST,
            started_at=int(datetime.now().timestamp()),
        )
        session.add(job)
        session.commit()
        try:
            job.generated = self.generate(agent, prompt)
            job.state = JobState.COMPLETE
        except llm.UnknownModelError as ue:
            job.state = JobState.FAIL
        finally:
            job.finished_at = int(datetime.now().timestamp())
        session.commit()
        return job
