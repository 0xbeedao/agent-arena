import os

from dependency_injector import containers
from dependency_injector import providers

from agentarena.actors.controllers.agent_controller import AgentController
from agentarena.actors.controllers.generatejob_controller import GenerateJobController
from agentarena.actors.controllers.strategy_controller import StrategyController
from agentarena.actors.models import Agent
from agentarena.actors.models import AgentCreate
from agentarena.actors.models import Strategy
from agentarena.actors.models import StrategyCreate
from agentarena.actors.models import StrategyPrompt
from agentarena.actors.models import StrategyPromptCreate
from agentarena.actors.services.template_service import TemplateService
from agentarena.clients.message_broker import MessageBroker
from agentarena.clients.message_broker import get_message_broker_connection
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services import uuid_service
from agentarena.core.services.db_service import DbService
from agentarena.core.services.llm_service import LLMService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.job import GenerateJob
from agentarena.models.job import GenerateJobCreate


def get_wordlist(
    projectroot: str,
    word_file: str,
):
    filename = word_file.replace("<projectroot>", str(projectroot))
    return uuid_service.get_wordlist(filename)


class ActorContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    projectroot = providers.Resource(get_project_root)
    wordlist = providers.Resource(get_wordlist, projectroot, config.uuid.wordlist)
    prod = getattr(os.environ, "ARENA_ENV", "dev") == "prod"

    logging = providers.Singleton(
        LoggingService,
        capture=config.actor.logging.capture,
        level=config.actor.logging.level,
        prod=prod,
        name="actor",
        logger_levels=config.actor.logging.loggers,
    )

    message_broker_connection = providers.Resource(
        get_message_broker_connection,
        config.messagebroker.url,
        logging,
    )

    uuid_service = providers.Singleton(
        UUIDService,
        word_list=wordlist,
        prod=prod,
    )

    message_broker = providers.Singleton(
        MessageBroker,
        client=message_broker_connection,
        uuid_service=uuid_service,
        logging=logging,
    )

    db_service = providers.Singleton(
        DbService,
        projectroot,
        config.actor.db.filename,
        get_engine=get_engine,
        prod=prod,
        uuid_service=uuid_service,
        logging=logging,
    )

    # model services

    agent_service = providers.Singleton(
        ModelService[Agent, AgentCreate],
        model_class=Agent,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )

    strategy_service = providers.Singleton(
        ModelService[Strategy, StrategyCreate],
        model_class=Strategy,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )

    strategyprompt_service = providers.Singleton(
        ModelService[StrategyPrompt, StrategyPromptCreate],
        model_class=StrategyPrompt,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )

    generatejob_service = providers.Singleton(
        ModelService[GenerateJob, GenerateJobCreate],
        model_class=GenerateJob,
        db_service=db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )

    # other services

    llm_service = providers.Singleton(
        LLMService,
        db_service,
        message_broker=message_broker,
        uuid_service=uuid_service,
        logging=logging,
    )

    template_service = providers.Singleton(
        TemplateService,
        strategy_service=strategy_service,
        logging=logging,
    )

    # Controllers

    agent_controller = providers.Singleton(
        AgentController,
        agent_service=agent_service,
        job_service=generatejob_service,
        llm_service=llm_service,
        message_broker=message_broker,
        template_service=template_service,
        uuid_service=uuid_service,
        logging=logging,
    )

    generatejob_controller = providers.Singleton(
        GenerateJobController,
        llm_service=llm_service,
        model_service=generatejob_service,
        template_service=template_service,
        uuid_service=uuid_service,
        logging=logging,
    )

    strategy_controller = providers.Singleton(
        StrategyController,
        message_broker=message_broker,
        prompt_service=strategyprompt_service,
        strategy_service=strategy_service,
        template_service=template_service,
        uuid_service=uuid_service,
        logging=logging,
    )
