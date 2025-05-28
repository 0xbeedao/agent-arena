import os

from dependency_injector import containers
from dependency_injector import providers

from agentarena.actors.controllers.responder_controller import ResponderController
from agentarena.actors.models import Agent
from agentarena.actors.models import AgentCreate
from agentarena.actors.models import AgentPublic
from agentarena.actors.models import AgentUpdate
from agentarena.actors.models import Strategy
from agentarena.actors.models import StrategyCreate
from agentarena.actors.models import StrategyPublic
from agentarena.actors.models import StrategyUpdate
from agentarena.clients.message_broker import (
    MessageBroker,
    get_message_broker_connection,
)
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services import uuid_service
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService


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
        uuid_service=uuid_service,
        logging=logging,
    )

    strategy_service = providers.Singleton(
        ModelService[Strategy, StrategyCreate],
        model_class=Strategy,
        db_service=db_service,
        uuid_service=uuid_service,
        logging=logging,
    )

    # Controllers

    agent_controller = providers.Singleton(
        ModelController[Agent, AgentCreate, AgentUpdate, AgentPublic],
        model_name="agent",
        model_create=AgentCreate,
        model_update=AgentUpdate,
        model_public=AgentPublic,
        model_service=agent_service,
        logging=logging,
    )

    responder_controller = providers.Singleton(
        ResponderController,
        agent_service=agent_service,
        logging=logging,
    )

    strategy_controller = providers.Singleton(
        ModelController[Strategy, StrategyCreate, StrategyUpdate, StrategyPublic],
        model_name="strategy",
        model_create=StrategyCreate,
        model_public=StrategyPublic,
        model_update=StrategyUpdate,
        model_service=strategy_service,
        logging=logging,
    )
