from dependency_injector import containers, providers
from sqlite_utils.db import Database
from pathlib import Path

from agentarena.services.strategy_service import StrategyService
from .logger import setup_logging
from agentarena.services.db_service import DbService
from agentarena.services.agent_service import AgentService

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

    agent_service = providers.Singleton(
        AgentService,
        db_service
    )

    strategy_service = providers.Singleton(
        StrategyService,
        db_service
    )


