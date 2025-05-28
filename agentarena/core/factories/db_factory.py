from sqlmodel import create_engine


def get_engine(filename: str, memory: bool = False):
    fname = ":memory:" if memory else filename
    dbfile = f"sqlite:///{fname}"

    connect_args = {"check_same_thread": False}
    return create_engine(dbfile, echo=False, connect_args=connect_args)
