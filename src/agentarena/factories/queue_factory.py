from litequeue import LiteQueue


def get_queue(filename: str, memory: bool = False) -> LiteQueue:
    dbfile = ":memory:" if memory else filename

    return LiteQueue(dbfile)
