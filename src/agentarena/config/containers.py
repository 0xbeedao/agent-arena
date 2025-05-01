from dependency_injector import containers, providers
from sqlite_utils.db import Database
from pathlib import Path

from agentarena.models.feature import Feature


from .logger import setup_logging
from agentarena.models.agent import AgentConfig
from agentarena.models.arena import ArenaConfig, ArenaAgent
from agentarena.models.contest import Contest
from agentarena.models.stats import RoundStats
from agentarena.models.strategy import Strategy
from agentarena.services.db_service import DbService
from agentarena.services.model_service import ModelService

def get_database(filename: str, memory: bool = False) -> Database:
    if memory:
        return Database(memory=True)
    
    print (f"opening db at: {filename}")
    return Database(filename)

def get_project_root():
    root = Path(__file__).parent.parent.parent.parent
    print (f"root: {root}")
    return root

class Container(containers.DeclarativeContainer):

    config = providers.Configuration()

    projectroot = providers.Resource(
        get_project_root
    )

    logging = providers.Resource(
        setup_logging
    )

    get_db = providers.Factory(
        get_database
    )

    db_service = providers.Singleton(
        DbService,
        projectroot,
        config.db.filename,
        get_database
    )

    # model services
    
    agent_service = providers.Singleton(
        ModelService[AgentConfig],
        model_class=AgentConfig,
        dbService=db_service,
        table_name="agents"
    )

    arena_service = providers.Singleton(
        ModelService[ArenaConfig],
        model_class=ArenaConfig,
        dbService=db_service,
        table_name="arenas"
    )

    arenaagent_service = providers.Singleton(
        ModelService[ArenaAgent],
        model_class=ArenaAgent,
        dbService=db_service,
        table_name="arena_agents"
    )

    contest_service = providers.Singleton(
        ModelService[Contest],
        model_class=Contest,
        dbService=db_service,
        table_name="contests"
    )

    feature_service = providers.Singleton(
        ModelService[Feature],
        model_class=Feature,
        dbService=db_service,
        table_name="features"
    )

    roundstats_service = providers.Singleton(
        ModelService[RoundStats],
        model_class=RoundStats,
        dbService=db_service,
        table_name="roundstats"
    )

    strategy_service = providers.Singleton(
        ModelService[Strategy],
        model_class=Strategy,
        dbService=db_service,
        table_name="strategies"
    )


