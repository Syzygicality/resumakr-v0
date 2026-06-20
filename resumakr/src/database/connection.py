import sqlite3
import functools
from pathlib import Path

DB_PATH = Path(__file__).parent / "resumakr.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS resumes (
    id         INTEGER PRIMARY KEY,
    label      TEXT NOT NULL UNIQUE,
    content    TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS tags (
    id   INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS resume_tags (
    resume_id INTEGER REFERENCES resumes(id) ON DELETE CASCADE,
    tag_id    INTEGER REFERENCES tags(id) ON DELETE CASCADE,
    PRIMARY KEY (resume_id, tag_id)
);
"""


def init_db() -> bool:
    """Create resumakr.db and apply the schema if the file does not exist. Returns True if created."""
    if DB_PATH.exists():
        return False
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    return True


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db(fn):
    """
    Inject a sqlite3.Connection as the first argument of a CRUD function.

    The wrapped function must declare `db` as its first parameter.
    A fresh connection is opened before the call and closed (with commit
    on success, rollback on error) afterwards.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        db = get_connection()
        try:
            result = fn(db, *args, **kwargs)
            db.commit()
            return result
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    return wrapper
