import sqlite3
import functools
from pathlib import Path

DB_PATH = Path(__file__).parent / "resumakr.db"


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
