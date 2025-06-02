import json
from jinja2 import Environment
from jinja2 import PackageLoader
from jinja2 import TemplateNotFound
from jinja2 import select_autoescape
from sqlmodel import Session, select

from agentarena.actors.models import Agent, Strategy, StrategyCreate, StrategyPrompt
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.model_service import ModelService
from agentarena.models.requests import ParticipantRequest


class InvalidTemplateException(Exception):
    pass


class TemplateService:
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
        self.env = Environment(
            loader=PackageLoader("agentarena.actors"), autoescape=select_autoescape()
        )
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
        self, strategy_id: str, command: str, session: Session
    ) -> StrategyPrompt:
        stmt = (
            select(StrategyPrompt)
            .where(StrategyPrompt.strategy_id == strategy_id)
            .where(StrategyPrompt.key == command)
        )
        prompt = session.exec(stmt).first()
        if not prompt:
            raise InvalidTemplateException(
                f"No such template {command} for strategy {strategy_id}"
            )
        return prompt

    def get_template(self, key: str):
        possibles = [key, f"{key}.md", f"{key}.md.j2"]
        try:
            return self.env.select_template(possibles)
        except TemplateNotFound as te:
            self.log.error("could not find template", key=key)
            raise InvalidTemplateException(key)

    def render_template(self, key, data: object) -> str:
        """
        Render the template by key, with the kwargs as values
        """
        return self.get_template(key).render(data)
