from contextlib import contextmanager
import sqlite3
from backend.config import settings

SCHEMA_FILE = settings.database_path.parent / "schema" / "schema.sql"

def initialize_database() -> None:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    schema = SCHEMA_FILE.read_text(encoding="utf-8")
    with sqlite3.connect(settings.database_path) as connection:
        connection.executescript(schema)
        connection.commit()

@contextmanager
def db_connection():
    connection = sqlite3.connect(settings.database_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
