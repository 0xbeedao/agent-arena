import json

from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import TemplateNotFound
from jinja2 import select_autoescape
from sqlmodel import Session
from sqlmodel import select

from agentarena.actors.models import Agent
from agentarena.actors.models import Strategy
from agentarena.actors.models import StrategyCreate
from agentarena.actors.models import StrategyPrompt
from agentarena.core.exceptions import InvalidTemplateException
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.models.constants import PromptType
from agentarena.models.requests import ParticipantRequest
from agentarena.util.jinja_helpers import datetimeformat_filter


class TemplateService(JinjaRenderer):
    """
    Provides template filling services, using Jinja2
    """

    def __init__(
        self,
        strategy_service: ModelService[Strategy, StrategyCreate],
        logging: LoggingService,
    ):

        self.strategy_service = strategy_service
        self.log = logging.get_logger("service")
        super().__init__()
        self.log.debug("Found templates", templates=self.env.list_templates())

    async def expand_prompt(
        self, agent: Agent, req: ParticipantRequest, session: Session
    ) -> str:
        """
        Takes the prompt from the request and expand it using Jinja. Not sure what controller should do this.
        """
        strategy_id = agent.strategy_id
        log = self.log.bind(job=req.job_id, cmd=req.command, agent=agent.id)
        strategy_prompt = await self.get_prompt(strategy_id, req.command, session)
        prompt = strategy_prompt.prompt
        if prompt.startswith("#jinja:"):
            key = prompt.replace("#jinja:", "")
            data = json.loads(req.data)
            data["agent"] = agent
            log.info("Rendering template for prompt", template=key)
            return self.render_template(key, data)
        else:
            log.info("Returning raw prompt")
            return prompt

    async def get_prompt(
        self, strategy_id: str, prompt_type: PromptType, session: Session
    ) -> StrategyPrompt:
        stmt = (
            select(StrategyPrompt)
            .where(StrategyPrompt.strategy_id == strategy_id)
            .where(StrategyPrompt.key == prompt_type)
        )
        prompt = session.exec(stmt).first()
        if not prompt:
            raise InvalidTemplateException(
                f"No such template {prompt_type.value} for strategy {strategy_id}"
            )
        return prompt
