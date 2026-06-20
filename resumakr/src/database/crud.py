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


@get_db
def find_resumes_by_label(db: Connection, substring: str) -> list[dict]:
    rows = db.execute(
        "SELECT label, content FROM resumes WHERE label LIKE ?",
        (f"%{substring}%",),
    ).fetchall()
    return [dict(row) for row in rows]


@get_db
def delete_resume(db: Connection, label: str) -> None:
    db.execute("DELETE FROM resumes WHERE label = ?", (label,))


@get_db
def save_resume(db: Connection, label: str, content: str, tags: list[str]) -> None:
    db.execute(
        """
        INSERT INTO resumes (label, content)
        VALUES (?, ?)
        ON CONFLICT(label) DO UPDATE
            SET content    = excluded.content,
                updated_at = datetime('now')
        """,
        (label, content),
    )
    resume_id = db.execute(
        "SELECT id FROM resumes WHERE label = ?", (label,)
    ).fetchone()[0]

    for name in tags:
        db.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (name,))
        tag_id = db.execute("SELECT id FROM tags WHERE name = ?", (name,)).fetchone()[0]
        db.execute(
            "INSERT OR IGNORE INTO resume_tags (resume_id, tag_id) VALUES (?, ?)",
            (resume_id, tag_id),
        )
