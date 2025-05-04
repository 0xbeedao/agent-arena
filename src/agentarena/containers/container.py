from pathlib import Path

import httpx
from dependency_injector import containers
from dependency_injector import providers

from .db import get_database
from .queue import get_queue
from .environment import get_project_root
from agentarena.models.agent import AgentDTO
from agentarena.models.arena import ArenaDTO
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.contest import ContestDTO
from agentarena.models.feature import FeatureDTO
from agentarena.models.state import ArenaStateDTO
from agentarena.models.stats import RoundStatsDTO
from agentarena.models.strategy import StrategyDTO
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService
from agentarena.services.queue_service import QueueService

from .logger import setup_logging


class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    projectroot = providers.Resource(get_project_root)

    logging = providers.Resource(setup_logging)

    get_q = providers.Factory(get_queue)

    db_service = providers.Singleton(
        DbService, projectroot, config.db.filename, get_database
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
    )

    arena_service = providers.Singleton(
        ModelService[ArenaDTO],
        model_class=ArenaDTO,
        dbService=db_service,
        table_name="arenas",
    )

    arenaagent_service = providers.Singleton(
        ModelService[ArenaAgentDTO],
        model_class=ArenaAgentDTO,
        dbService=db_service,
        table_name="arena_agents",
    )

    arenastate_service = providers.Singleton(
        ModelService[ArenaStateDTO],
        model_class=ArenaStateDTO,
        dbService=db_service,
        table_name="arena_states",
    )

    contest_service = providers.Singleton(
        ModelService[ContestDTO],
        model_class=ContestDTO,
        dbService=db_service,
        table_name="contests",
    )

    feature_service = providers.Singleton(
        ModelService[FeatureDTO],
        model_class=FeatureDTO,
        dbService=db_service,
        table_name="features",
    )

    roundstats_service = providers.Singleton(
        ModelService[RoundStatsDTO],
        model_class=RoundStatsDTO,
        dbService=db_service,
        table_name="roundstats",
    )

    strategy_service = providers.Singleton(
        ModelService[StrategyDTO],
        model_class=StrategyDTO,
        dbService=db_service,
        table_name="strategies",
    )

    http_client = providers.Factory(httpx.Client)
