from sqlite3 import Connection

from resumakr.src.database.connection import get_db


@get_db
def list_resumes(db: Connection) -> list[dict]:
    rows = db.execute(
        """
        SELECT r.id, r.label, r.created_at, r.updated_at,
               GROUP_CONCAT(t.name, ', ') AS tags
        FROM resumes r
        LEFT JOIN resume_tags rt ON r.id = rt.resume_id
        LEFT JOIN tags t ON rt.tag_id = t.id
        GROUP BY r.id
        ORDER BY r.id
        """
    ).fetchall()
    return [dict(row) for row in rows]
