import os

from dependency_injector import containers
from dependency_injector import providers

from agentarena.actors.controllers.actor_controller import ActorController
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.services import uuid_service
from agentarena.core.factories.db_factory import get_database
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.actors.models import (
    Agent,
    AgentCreate,
    AgentPublic,
    AgentUpdate,
    Strategy,
    StrategyCreate,
    StrategyUpdate,
    StrategyPublic,
)


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

    uuid_service = providers.Singleton(
        UUIDService,
        word_list=wordlist,
        prod=prod,
    )

    db_service = providers.Singleton(
        DbService,
        projectroot,
        config.actor.db.filename,
        get_database=get_database,
        prod=prod,
        uuid_service=uuid_service,
        logging=logging,
    )

    # model services

    agent_service = providers.Singleton(
        ModelService[Agent],
        model_class=Agent,
        db_service=db_service,
        logging=logging,
    )

    strategy_service = providers.Singleton(
        ModelService[Strategy],
        model_class=Strategy,
        db_service=db_service,
        logging=logging,
    )

    # Controllers

    agent_controller = providers.Singleton(
        ModelController[Agent, AgentCreate, AgentUpdate, AgentPublic],
        model_name="agent",
        model_service=agent_service,
        model_public=AgentPublic,
        logging=logging,
    )

    responder_controller = providers.Singleton(
        ResponderController,
        participant_service=participant_service,
        participant_factory=participant_factory,
        logging=logging,
    )

    strategy_controller = providers.Singleton(
        ModelController[Strategy, StrategyCreate, StrategyUpdate, StrategyPublic],
        model_name="strategy",
        model_service=strategy_service,
        logging=logging,
    )
