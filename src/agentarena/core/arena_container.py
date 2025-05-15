import os

from dependency_injector import containers
from dependency_injector import providers

from agentarena.controllers.arena_controller import ArenaController
from agentarena.controllers.contest_controller import ContestController
from agentarena.controllers.debug_controller import DebugController
from agentarena.controllers.model_controller import ModelController
from agentarena.controllers.responder_controller import ResponderController
from agentarena.factories.arena_factory import ArenaFactory
from agentarena.factories.contest_factory import ContestFactory
from agentarena.factories.db_factory import get_database
from agentarena.factories.environment_factory import get_project_root
from agentarena.factories.logger_factory import LoggingService
from agentarena.factories.participant_factory import ParticipantFactory
from agentarena.models.agent import AgentDTO
from agentarena.models.arena import ArenaDTO
from agentarena.models.contest import ContestDTO
from agentarena.models.event import JobEvent
from agentarena.models.feature import FeatureDTO
from agentarena.models.job import CommandJob
from agentarena.models.job import CommandJobHistory
from agentarena.models.participant import ParticipantDTO
from agentarena.models.state import ArenaStateDTO
from agentarena.models.stats import RoundStatsDTO
from agentarena.models.strategy import StrategyDTO
from agentarena.services import uuid_service
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService
from agentarena.services.uuid_service import UUIDService


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

    jobevent_service = providers.Singleton(
        ModelService[JobEvent],
        model_class=JobEvent,
        db_service=db_service,
        table_name="jobevent",
        logging=logging,
    )

    agent_service = providers.Singleton(
        ModelService[AgentDTO],
        model_class=AgentDTO,
        db_service=db_service,
        table_name="agents",
        logging=logging,
    )

    arena_service = providers.Singleton(
        ModelService[ArenaDTO],
        model_class=ArenaDTO,
        db_service=db_service,
        table_name="arenas",
        logging=logging,
    )

    participant_service = providers.Singleton(
        ModelService[ParticipantDTO],
        model_class=ParticipantDTO,
        db_service=db_service,
        table_name="participants",
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
        ModelService[ContestDTO],
        model_class=ContestDTO,
        db_service=db_service,
        table_name="contests",
        logging=logging,
    )

    feature_service = providers.Singleton(
        ModelService[FeatureDTO],
        model_class=FeatureDTO,
        db_service=db_service,
        table_name="features",
        logging=logging,
    )

    commandjob_service = providers.Singleton(
        ModelService[CommandJob],
        model_class=CommandJob,
        db_service=db_service,
        table_name="jobs",
        logging=logging,
    )

    roundstats_service = providers.Singleton(
        ModelService[RoundStatsDTO],
        model_class=RoundStatsDTO,
        db_service=db_service,
        table_name="roundstats",
        logging=logging,
    )

    strategy_service = providers.Singleton(
        ModelService[StrategyDTO],
        model_class=StrategyDTO,
        db_service=db_service,
        table_name="strategies",
        logging=logging,
    )

    jobhistory_service = providers.Singleton(
        ModelService[CommandJobHistory],
        model_class=CommandJobHistory,
        db_service=db_service,
        table_name="jobhistories",
        logging=logging,
    )

    queue_service = providers.Singleton(
        QueueService,
        history_service=jobhistory_service,
        job_service=commandjob_service,
        logging=logging,
    )

    # factory services

    participant_factory = providers.Singleton(
        ParticipantFactory,
        agent_service=agent_service,
        logging=logging,
    )

    arena_factory = providers.Singleton(
        ArenaFactory,
        participant_service=participant_service,
        feature_service=feature_service,
        participant_factory=participant_factory,
        logging=logging,
    )

    contest_factory = providers.Singleton(
        ContestFactory,
        arena_service=arena_service,
        participant_service=participant_service,
        participant_factory=participant_factory,
        arena_factory=arena_factory,
        logging=logging,
    )

    # controllers

    agent_controller = providers.Singleton(
        ModelController[AgentDTO],
        model_name="agent",
        model_service=agent_service,
        logging=logging,
    )

    arena_controller = providers.Singleton(
        ArenaController,
        model_service=arena_service,
        agent_service=agent_service,
        feature_service=feature_service,
        participant_service=participant_service,
        arena_factory=arena_factory,
        logging=logging,
    )

    contest_controller = providers.Singleton(
        ContestController,
        model_service=contest_service,
        contest_factory=contest_factory,
        logging=logging,
    )

    responder_controller = providers.Singleton(
        ResponderController,
        participant_service=participant_service,
        participant_factory=participant_factory,
        logging=logging,
    )

    strategy_controller = providers.Singleton(
        ModelController[StrategyDTO],
        model_name="strategy",
        model_service=strategy_service,
        logging=logging,
    )

    debug_controller = providers.Singleton(
        DebugController,
        agent_service=agent_service,
        queue_service=queue_service,
        job_service=commandjob_service,
        logging=logging,
    )
