import sqlite3
from contextlib import contextmanager
from backend.config import settings
def init_db():
 settings.db.parent.mkdir(parents=True,exist_ok=True)
 with sqlite3.connect(settings.db) as d:d.executescript((settings.db.parent/'schema.sql').read_text())
@contextmanager
def connect():
 d=sqlite3.connect(settings.db);d.row_factory=sqlite3.Row
 try:yield d;d.commit()
 finally:d.close()
