from dependency_injector import containers, providers
from sqlite_utils.db import Database
from pathlib import Path

from agentarena.services.model_service import ModelService
from .logger import setup_logging
from agentarena.services.db_service import DbService
from agentarena.models.agent import AgentConfig
from agentarena.models.strategy import Strategy

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
        ModelService[AgentConfig],
        model_class=AgentConfig,
        dbService=db_service,
        table_name="agents"
    )

    strategy_service = providers.Singleton(
        ModelService[Strategy],
        model_class=Strategy,
        dbService=db_service,
        table_name="strategies"
    )


