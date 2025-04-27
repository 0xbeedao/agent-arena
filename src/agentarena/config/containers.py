from dependency_injector import containers, providers
from sqlite_utils.db import Database
from pathlib import Path
from .logger import setup_logging

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

    get_database = providers.Callable(
        get_database
    )

    logging = providers.Resource(
        setup_logging
    )

