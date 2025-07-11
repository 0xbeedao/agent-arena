import os

from dependency_injector import containers
from dependency_injector import providers

from agentarena.arena.controllers.arena_controller import ArenaController
from agentarena.arena.controllers.contest_controller import ContestController
from agentarena.arena.controllers.debug_controller import DebugController
from agentarena.arena.models import Arena
from agentarena.arena.models import ArenaCreate
from agentarena.arena.models import Contest
from agentarena.arena.models import ContestCreate
from agentarena.arena.models import ContestRound
from agentarena.arena.models import ContestRoundStats
from agentarena.arena.models import Feature
from agentarena.arena.models import FeatureCreate
from agentarena.arena.models import JudgeResult
from agentarena.arena.models import JudgeResultCreate
from agentarena.arena.models import Participant
from agentarena.arena.models import ParticipantCreate
from agentarena.arena.models import ParticipantPublic
from agentarena.arena.models import ParticipantUpdate
from agentarena.arena.models import PlayerAction
from agentarena.arena.models import PlayerActionCreate
from agentarena.arena.models import PlayerState
from agentarena.arena.models import PlayerStateCreate
from agentarena.arena.services.round_service import RoundService
from agentarena.arena.services.view_service import ViewService
from agentarena.clients.message_broker import MessageBroker
from agentarena.clients.message_broker import get_message_broker_connection
from agentarena.core.controllers.model_controller import ModelController
from agentarena.core.factories.db_factory import get_engine
from agentarena.core.factories.environment_factory import get_project_root
from agentarena.core.factories.logger_factory import LoggingService
from agentarena.core.services import uuid_service
from agentarena.core.services.db_service import DbService
from agentarena.core.services.jinja_renderer import JinjaRenderer
from agentarena.core.services.model_service import ModelService
from agentarena.core.services.uuid_service import UUIDService


def get_logfile(
    projectroot: str,
    config: str,
):
    filename = config.replace("<projectroot>", str(projectroot))
    return (
        os.path.join(projectroot, filename)
        if not filename.startswith("/")
        else filename
    )


def get_wordlist(
    projectroot: str,
    word_file: str,
):
    filename = word_file.replace("<projectroot>", str(projectroot))
    return uuid_service.get_wordlist(filename)


class ArenaContainer(containers.DeclarativeContainer):

    config = providers.Configuration()
    prod = getattr(os.environ, "ARENA_ENV", "dev") == "prod"

    projectroot = providers.Resource(get_project_root)
    logfile = get_logfile = providers.Resource(
        get_logfile,
        projectroot=projectroot,
        config=config.arena.logging.logfile,
    )
    wordlist = providers.Resource(
        get_wordlist,
        projectroot,
        config.uuid.wordlist,
    )

    logging = providers.Singleton(
        LoggingService,
        capture=config.arena.logging.capture,
        level=config.arena.logging.level,
        prod=prod,
        name="arena",
        logfile=logfile,
        logger_levels=config.arena.logging.loggers,
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
        config.arena.db.filename,
        get_engine=get_engine,
        prod=prod,
        uuid_service=uuid_service,
        logging=logging,
    )

    # model services

    arena_service = providers.Singleton(
        ModelService[Arena, ArenaCreate],
        model_class=Arena,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    participant_service = providers.Singleton(
        ModelService[Participant, ParticipantCreate],
        model_class=Participant,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    arenastate_service = providers.Singleton(
        ModelService[ContestRound, ContestRound],
        model_class=ContestRound,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    contest_service = providers.Singleton(
        ModelService[Contest, ContestCreate],
        model_class=Contest,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    playeraction_service = providers.Singleton(
        ModelService[PlayerAction, PlayerActionCreate],
        model_class=PlayerAction,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    judge_result_service = providers.Singleton(
        ModelService[JudgeResult, JudgeResultCreate],
        model_class=JudgeResult,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    playerstate_service = providers.Singleton(
        ModelService[PlayerState, PlayerStateCreate],
        model_class=PlayerState,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    round_service = providers.Singleton(
        RoundService,
        db_service=db_service,
        playerstate_service=playerstate_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    feature_service = providers.Singleton(
        ModelService[Feature, FeatureCreate],
        model_class=Feature,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    contestroundstats_service = providers.Singleton(
        ModelService[ContestRoundStats, ContestRound],
        model_class=ContestRoundStats,
        db_service=db_service,
        message_broker=message_broker,
        message_prefix="sys.arena",
        uuid_service=uuid_service,
        logging=logging,
    )

    template_service = providers.Singleton(
        JinjaRenderer,
    )

    view_service = providers.Singleton(
        ViewService,
        logging=logging,
    )

    # controllers

    arena_controller = providers.Singleton(
        ArenaController,
        arena_service=arena_service,
        feature_service=feature_service,
        template_service=template_service,
        logging=logging,
    )

    participant_controller = providers.Singleton(
        ModelController[
            Participant, ParticipantCreate, ParticipantUpdate, ParticipantPublic
        ],
        base_path="/api/participant",
        model_name="participant",
        model_create=ParticipantCreate,
        model_update=ParticipantUpdate,
        model_public=ParticipantPublic,
        model_service=participant_service,
        template_service=template_service,
        logging=logging,
    )

    contest_controller = providers.Singleton(
        ContestController,
        playeraction_service=playeraction_service,
        player_state_service=playerstate_service,
        feature_service=feature_service,
        template_service=template_service,
        message_broker=message_broker,
        model_service=contest_service,
        participant_service=participant_service,
        round_service=round_service,
        view_service=view_service,
        logging=logging,
        judge_result_service=judge_result_service,
    )

    debug_controller = providers.Singleton(
        DebugController,
        logging=logging,
    )
