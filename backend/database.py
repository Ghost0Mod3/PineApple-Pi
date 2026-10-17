import sqlite3
from .config import settings

def connect():
    settings.database.parent.mkdir(parents=True,exist_ok=True)
    db=sqlite3.connect(settings.database)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    return db

def init_db():
    schema=(settings.database.parent/'schema.sql').read_text()
    with connect() as db: db.executescript(schema)
