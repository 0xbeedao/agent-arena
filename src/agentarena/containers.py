import httpx
from dependency_injector import containers
from dependency_injector import providers

from agentarena.controllers.arena_controller import ArenaController
from agentarena.controllers.contest_controller import ContestController
from agentarena.controllers.model_controller import ModelController
from agentarena.controllers.responder_controller import ResponderController
from agentarena.factories.arena_factory import ArenaFactory
from agentarena.factories.contest_factory import ContestFactory
from agentarena.factories.db_factory import get_database
from agentarena.factories.environment_factory import get_project_root
from agentarena.factories.logger_factory import LoggingService
from agentarena.factories.participant_factory import ParticipantFactory
from agentarena.factories.queue_factory import get_queue
from agentarena.models.agent import AgentDTO
from agentarena.models.arena import ArenaDTO
from agentarena.models.contest import ContestDTO
from agentarena.models.feature import FeatureDTO
from agentarena.models.job import JsonRequestJob
from agentarena.models.participant import ParticipantDTO
from agentarena.models.state import ArenaStateDTO
from agentarena.models.stats import RoundStatsDTO
from agentarena.models.strategy import StrategyDTO
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService
from agentarena.services.request_service import RequestService
from agentarena.services.result_service import ResultService


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    projectroot = providers.Resource(get_project_root)

    logging = providers.Singleton(LoggingService)

    make_httpclient = providers.Factory(httpx.Client)

    get_q = providers.Factory(get_queue)

    db_service = providers.Singleton(
        DbService,
        projectroot,
        config.db.filename,
        get_database=get_database,
        logging=logging,
    )

    job_q_service = providers.Singleton(
        QueueService, projectroot, config.queues.jobs.filename, get_q
    )

    # model services

    agent_service = providers.Singleton(
        ModelService[AgentDTO],
        model_class=AgentDTO,
        dbService=db_service,
        table_name="agents",
        logging=logging,
    )

    arena_service = providers.Singleton(
        ModelService[ArenaDTO],
        model_class=ArenaDTO,
        dbService=db_service,
        table_name="arenas",
        logging=logging,
    )

    participant_service = providers.Singleton(
        ModelService[ParticipantDTO],
        model_class=ParticipantDTO,
        dbService=db_service,
        table_name="participants",
        logging=logging,
    )

    arenastate_service = providers.Singleton(
        ModelService[ArenaStateDTO],
        model_class=ArenaStateDTO,
        dbService=db_service,
        table_name="arena_states",
        logging=logging,
    )

    contest_service = providers.Singleton(
        ModelService[ContestDTO],
        model_class=ContestDTO,
        dbService=db_service,
        table_name="contests",
        logging=logging,
    )

    feature_service = providers.Singleton(
        ModelService[FeatureDTO],
        model_class=FeatureDTO,
        dbService=db_service,
        table_name="features",
        logging=logging,
    )

    requestjob_service = providers.Singleton(
        ModelService[JsonRequestJob],
        model_class=JsonRequestJob,
        dbService=db_service,
        table_name="jsonjob",
        logging=logging,
    )

    roundstats_service = providers.Singleton(
        ModelService[RoundStatsDTO],
        model_class=RoundStatsDTO,
        dbService=db_service,
        table_name="roundstats",
        logging=logging,
    )

    strategy_service = providers.Singleton(
        ModelService[StrategyDTO],
        model_class=StrategyDTO,
        dbService=db_service,
        table_name="strategies",
        logging=logging,
    )

    job_service = providers.Singleton(
        requestjob_service=requestjob_service,
        logging=logging,
    )

    result_service = providers.Singleton(
        ResultService,
        logging=logging,
    )

    request_service = providers.Singleton(
        RequestService,
        queue_service=job_q_service,
        http_client_factory=make_httpclient,
        result_handler=result_service,
        logging=logging,
    )

    # factory services

    participant_factory = providers.Singleton(
        ParticipantFactory,
        agent_service=agent_service,
        strategy_service=strategy_service,
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
        ModelController[AgentDTO](
            model_name="agent", model_service=agent_service, logging=logging
        )
    )

    arena_controller = providers.Singleton(
        ArenaController(
            model_service=arena_service,
            agent_service=agent_service,
            feature_service=feature_service,
            participant_service=participant_service,
            arena_factory=arena_factory,
            logging=logging,
        )
    )

    contest_controller = providers.Singleton(
        ContestController,
        model_service=contest_service,
        contest_factory=contest_factory,
        logging=logging,
    )

    responder_controller = providers.Singleton(
        ResponderController, participant_service=participant_service, logging=logging
    )

    strategy_controller = providers.Singleton(
        ModelController[StrategyDTO](
            model_name="strategy", model_service=strategy_service, logging=logging
        )
    )
