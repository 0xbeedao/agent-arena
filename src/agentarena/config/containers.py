from dependency_injector import containers, providers
from sqlite_utils.db import Database
from pathlib import Path

from agentarena.models.feature import FeatureDTO


from .logger import setup_logging
from agentarena.models.agent import AgentDTO
from agentarena.models.arena import ArenaDTO
from agentarena.models.arenaagent import ArenaAgentDTO
from agentarena.models.contest import ContestDTO
from agentarena.models.stats import RoundStatsDTO
from agentarena.models.strategy import StrategyDTO
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
        ModelService[AgentDTO],
        model_class=AgentDTO,
        dbService=db_service,
        table_name="agents"
    )

    arena_service = providers.Singleton(
        ModelService[ArenaDTO],
        model_class=ArenaDTO,
        dbService=db_service,
        table_name="arenas"
    )

    arenaagent_service = providers.Singleton(
        ModelService[ArenaAgentDTO],
        model_class=ArenaAgentDTO,
        dbService=db_service,
        table_name="arena_agents"
    )

    contest_service = providers.Singleton(
        ModelService[ContestDTO],
        model_class=ContestDTO,
        dbService=db_service,
        table_name="contests"
    )

    feature_service = providers.Singleton(
        ModelService[FeatureDTO],
        model_class=FeatureDTO,
        dbService=db_service,
        table_name="features"
    )

    roundstats_service = providers.Singleton(
        ModelService[RoundStatsDTO],
        model_class=RoundStatsDTO,
        dbService=db_service,
        table_name="roundstats"
    )

    strategy_service = providers.Singleton(
        ModelService[StrategyDTO],
        model_class=StrategyDTO,
        dbService=db_service,
        table_name="strategies"
    )


