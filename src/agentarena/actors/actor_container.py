import os

from dependency_injector import containers
from dependency_injector import providers

from agentarena.actors.controllers.actor_controller import ActorController
from agentarena.core.factories.db_factory import get_database
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.factories.environment_factory import get_project_root
from agentarena.models.actor import ActorDTO
from agentarena.services import uuid_service


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

    logging = providers.Singleton(
        LoggingService,
        capture=config.actor.logging.capture,
        level=config.actor.logging.level,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
        name="actor",
        logger_levels=config.actor.logging.loggers,
    )

    uuid_service = providers.Singleton(
        UUIDService,
        word_list=wordlist,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
    )

    db_service = providers.Singleton(
        DbService,
        projectroot,
        config.actor.db.filename,
        get_database=get_database,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
        uuid_service=uuid_service,
        logging=logging,
    )

    # model services

    actor_service = providers.Singleton(
        ModelService(ActorDTO),
        model_claass=ActorDTO,
        db_service=db_service,
        table_name="actors",
        logging=logging,
    )

    # Controllers

    actor_controller = providers.Singleton(ActorController)
