from sqlite_utils import Database
from sqlmodel import create_engine


def get_database(filename: str, memory: bool = False) -> Database:
    if memory:
        return Database(memory=True)

    print(f"opening db at: {filename}")
    return Database(filename)


def get_engine(filename: str, memory: bool = False):
    fname = ":memory:" if memory else filename
    dbfile = f"sqlite:///{fname}"

    connect_args = {"check_same_thread": False}
    return create_engine(dbfile, echo=False, connect_args=connect_args)
