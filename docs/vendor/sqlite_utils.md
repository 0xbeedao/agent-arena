# sqlite-utils API Reference

This is a reference for the sqlite-utils Python library, which provides a convenient interface for working with SQLite databases.

## Database

The `Database` class is the main entry point for working with SQLite databases.

```python
from sqlite_utils import Database

# Create or open a database file
db = Database("data.db")

# Create an in-memory database
db = Database(memory=True)
```

## Tables and Queries

Access tables using dictionary-style access:

```python
# Get a reference to a table (creates it if it doesn't exist)
table = db["my_table"]

# Insert data
table.insert({"name": "Alice", "age": 30})
table.insert_all([
    {"name": "Bob", "age": 22},
    {"name": "Charlie", "age": 45}
])

# Query data
for row in table.rows:
    print(row)  # {'name': 'Alice', 'age': 30}, etc.

# Filter with SQL WHERE clauses
for row in table.rows_where("age > ?", [25]):
    print(row)
```

## Creating Tables

Create tables explicitly:

```python
db.create_table(
    "people",
    {
        "id": int,
        "name": str,
        "age": int,
        "weight": float
    },
    pk="id"
)
```

## Foreign Keys

```python
# Add a foreign key
db["dogs"].add_foreign_key("owner_id", "people", "id")

# Create a table with a foreign key
db.create_table(
    "dogs",
    {
        "id": int,
        "name": str,
        "owner_id": int
    },
    pk="id",
    foreign_keys=[("owner_id", "people", "id")]
)
```

## Full-text Search

```python
# Enable FTS on a table
db["books"].enable_fts(["title", "body"])

# Search
rows = list(db["books"].search("python programming"))
```

## Transactions

```python
with db.conn:  # Starts a transaction
    db["table"].insert({"name": "Data in transaction"})
    # Commits when the block exits normally, rolls back on exception
```

## Indexes

```python
# Create an index
db["people"].create_index(["name"])

# Create a unique index
db["people"].create_index(["email"], unique=True)
```

## Schema Modifications

```python
# Add a column
db["people"].add_column("email", str)

# Transform a table (e.g., rename columns)
db["people"].transform(
    rename={"name": "full_name"}
)
```

## Utilities

```python
# Get database schema
print(db.schema)

# List tables
print(db.table_names())

# Vacuum the database
db.vacuum()
```

For more detailed documentation, visit: https://sqlite-utils.datasette.io/
