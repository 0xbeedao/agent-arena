import os

from dependency_injector import containers
from dependency_injector import providers

from agentarena.actors.controllers.responder_controller import ResponderController
from agentarena.arena.controllers.arena_controller import ArenaController
from agentarena.arena.controllers.contest_controller import ContestController
from agentarena.arena.controllers.debug_controller import DebugController
from agentarena.arena.models.arena import Arena, Contest, Feature, Participant
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.db_factory import get_database
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services import uuid_service
from agentarena.core.services.db_service import DbService
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService
from agentarena.models.state import ArenaStateDTO
from agentarena.models.stats import RoundStatsDTO
from agentarena.scheduler.services.queue_service import QueueService


def get_wordlist(
    projectroot: str,
    word_file: str,
):
    filename = word_file.replace("<projectroot>", str(projectroot))
    return uuid_service.get_wordlist(filename)


class ArenaContainer(containers.DeclarativeContainer):

    config = providers.Configuration()

    projectroot = providers.Resource(get_project_root)
    wordlist = providers.Resource(get_wordlist, projectroot, config.uuid.wordlist)

    logging = providers.Singleton(
        LoggingService,
        capture=config.arena.logging.capture,
        level=config.arena.logging.level,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
        name="arena",
        logger_levels=config.arena.logging.loggers,
    )

    uuid_service = providers.Singleton(
        UUIDService,
        word_list=wordlist,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
    )

    db_service = providers.Singleton(
        DbService,
        projectroot,
        config.arena.db.filename,
        get_database=get_database,
        prod=getattr(os.environ, "ARENA_ENV", "dev") == "prod",
        uuid_service=uuid_service,
        logging=logging,
    )

    # model services

    arena_service = providers.Singleton(
        ModelService[Arena],
        model_class=Arena,
        db_service=db_service,
        logging=logging,
    )

    participant_service = providers.Singleton(
        ModelService[Participant],
        model_class=Participant,
        db_service=db_service,
        logging=logging,
    )

    arenastate_service = providers.Singleton(
        ModelService[ArenaStateDTO],
        model_class=ArenaStateDTO,
        db_service=db_service,
        table_name="arena_states",
        logging=logging,
    )

    contest_service = providers.Singleton(
        ModelService[Contest],
        model_class=Contest,
        db_service=db_service,
        logging=logging,
    )

    feature_service = providers.Singleton(
        ModelService[Feature],
        model_class=Feature,
        db_service=db_service,
        logging=logging,
    )

    roundstats_service = providers.Singleton(
        ModelService[RoundStatsDTO],
        model_class=RoundStatsDTO,
        db_service=db_service,
        table_name="roundstats",
        logging=logging,
    )

    # controllers

    arena_controller = providers.Singleton(
        ArenaController,
        arena_service=arena_service,
        feature_service=feature_service,
        logging=logging,
    )

    contest_controller = providers.Singleton(
        ContestController,
        model_service=contest_service,
        logging=logging,
    )

    debug_controller = providers.Singleton(
        DebugController,
        logging=logging,
    )
