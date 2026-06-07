import sqlite3
import functools
from pathlib import Path

DB_PATH = Path(__file__).parent / "resumakr.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def inject_connection(fn):
    """
    Inject a sqlite3.Connection as the first argument of a CRUD function.

    The wrapped function must declare `conn` as its first parameter.
    A fresh connection is opened before the call and closed (with commit
    on success, rollback on error) afterwards.
    """

    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        conn = get_connection()
        try:
            result = fn(conn, *args, **kwargs)
            conn.commit()
            return result
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    return wrapper
