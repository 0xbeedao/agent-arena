from sqlite_utils import Database


def get_database(filename: str, memory: bool = False) -> Database:
    if memory:
        return Database(memory=True)

    print(f"opening db at: {filename}")
    return Database(filename)
