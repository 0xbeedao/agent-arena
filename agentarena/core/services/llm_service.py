from sqlmodel import Field
from agentarena.clients.message_broker import MessageBroker
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.models.job import ControllerRequest


class LLMService:

    def __init__(
        self,
        message_broker: MessageBroker = Field(),
        logging: LoggingService = Field(),
    ):
        self.log = logging.get_logger("llm")
        self.message_broker = message_broker

    async def generate(self, req: ControllerRequest):
        pass
