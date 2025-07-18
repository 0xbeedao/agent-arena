import json

from jinja2 import ChoiceLoader
from jinja2 import PackageLoader
from sqlmodel import Session
from sqlmodel import select

from agentarena.actors.models import Agent
from agentarena.actors.models import Strategy
from agentarena.actors.models import StrategyCreate
from agentarena.actors.models import StrategyPrompt
from agentarena.core.exceptions import InvalidTemplateException
from agentarena.core.exceptions import TemplateRenderingException
from agentarena.core.exceptions import TemplateDataException
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.models.constants import PromptType
from agentarena.models.requests import ParticipantActionRequest
from agentarena.models.requests import ParticipantContestRequest
from agentarena.models.requests import ParticipantContestRoundRequest


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
        super().__init__(base_path="agentarena.core")

        # Add support for both template locations
        self.env.loader = ChoiceLoader(
            [
                PackageLoader("agentarena.core", "templates"),
                PackageLoader("agentarena.actors", "templates"),
            ]
        )

        self.log.debug("Found templates", templates=self.env.list_templates())

    async def expand_prompt(
        self,
        agent: Agent,
        job_id: str,
        req: (
            ParticipantContestRequest
            | ParticipantContestRoundRequest
            | ParticipantActionRequest
        ),
        session: Session,
    ) -> str:
        """
        Takes the prompt from the request and expand it using Jinja.
        """
        strategy_id = agent.strategy_id
        log = self.log.bind(job=job_id, cmd=req.command, agent=agent.id)
        strategy_prompt = await self.get_prompt(strategy_id, req.command, session)
        prompt = strategy_prompt.prompt
        if prompt.startswith("#jinja:"):
            key = prompt.replace("#jinja:", "")
            data = req.data.model_dump()
            data["agent"] = agent.get_public().model_dump()
            log = log.bind(template=key)
            log.info("Rendering template for prompt")
            try:
                return self.render_template(key, data)
            except (TemplateRenderingException, TemplateDataException) as e:
                # Log the structured error information
                log.error(
                    "Template rendering error",
                    error_type=type(e).__name__,
                    error_message=e.message,
                    template=key,
                    error_details=getattr(e, "error_details", None),
                    missing_field=getattr(e, "missing_field", None),
                    data_context=getattr(e, "data_context", {}),
                    data_keys=list(data.keys()),
                )

                # Save error data for debugging
                try:
                    with open("error_data.json", "w") as f:
                        json.dump(
                            {
                                "error_type": type(e).__name__,
                                "error_message": e.message,
                                "template": key,
                                "error_details": getattr(e, "error_details", None),
                                "missing_field": getattr(e, "missing_field", None),
                                "data_context": getattr(e, "data_context", {}),
                                "data": data,
                            },
                            f,
                            indent=2,
                            default=str,
                        )
                except Exception as save_error:
                    log.error("Failed to save error data", save_error=save_error)

                # Re-raise the exception to be handled by the controller
                raise e
            except Exception as e:
                # Handle any other unexpected errors
                log.error("Unexpected error rendering template", error=e, data=data)
                try:
                    with open("error_data.json", "w") as f:
                        json.dump(
                            {
                                "error_type": "UnexpectedError",
                                "error_message": str(e),
                                "template": key,
                                "data": data,
                            },
                            f,
                            indent=2,
                            default=str,
                        )
                except Exception as save_error:
                    log.error("Failed to save error data", save_error=save_error)
                raise e
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
