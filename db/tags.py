from typing import Optional, List, Sequence
from aqt import mw
from datetime import datetime, timezone
from ..model import FailureTag
# Schema:
# tags(tag_id INTEGER PK, name TEXT UNIQUE NOT NULL, created_at TEXT)
# failure_tags(failure_id FK -> failures.failure_id, tag_id FK -> tags.tag_id, UNIQUE pair)

TAGS_SQL = """
CREATE TABLE IF NOT EXISTS ft_tags (
    tag_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    created_at TEXT NOT NULL
)
"""
FAILURE_TAGS_SQL = """
CREATE TABLE IF NOT EXISTS ft_failure_tags (
    failure_id INTEGER NOT NULL REFERENCES failures(failure_id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES tags(tag_id) ON DELETE CASCADE,
    PRIMARY KEY (failure_id, tag_id)
)
"""
INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_tags_name ON ft_tags(name)",
    "CREATE INDEX IF NOT EXISTS idx_failure_tags_tag_id ON ft_failure_tags(tag_id)",
    "CREATE INDEX IF NOT EXISTS idx_failure_tags_failure_id ON ft_failure_tags(failure_id)",
]

def ensure_schema():
    db = mw.col.db
    db.execute(TAGS_SQL)
    db.execute(FAILURE_TAGS_SQL)
    for i in INDEXES:
        db.execute(i)

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# --- Tag operations ---

def add_tag(name: str) -> Optional[int]:
    """Insert new tag; return tag_id or existing id if already there."""
    name = name.strip()
    if not name:
        return None
    ensure_schema()
    mw.col.db.execute(
        "INSERT OR IGNORE INTO ft_tags(name, created_at) VALUES (?, ?)",
        name, _now_iso()
    )
    tag_id = mw.col.db.scalar("SELECT tag_id FROM tags WHERE name = ?", name)
    mw.col.setMod()
    return tag_id

def get_tag_id(name: str) -> Optional[int]:
    ensure_schema()
    return mw.col.db.scalar("SELECT tag_id FROM ft_tags WHERE name = ?", name.strip())

def tag_exists(id: int) -> bool:
    ensure_schema()
    return mw.col.db.scalar("SELECT tag_id FROM ft_tags WHERE tag_id = ?", id) is not None

def list_tags(limit: Optional[int] = None) -> List[FailureTag]:
    ensure_schema()
    sql = "SELECT tag_id, name FROM ft_tags ORDER BY name COLLATE NOCASE"
    params = []
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return [FailureTag(tag_id=r[0], name=r[1]) for r in mw.col.db.all(sql, *params)]

def delete_tag(name: str):
    """Remove tag and its associations."""
    ensure_schema()
    mw.col.db.execute("DELETE FROM ft_tags WHERE name = ?", name.strip())
    mw.col.setMod()

# --- Failure <-> Tag associations ---

def assign_tag_to_failure(failure_id: int, tag_id: int):
    """Attach tag to a failure (throws exception if tag doesnt exist)."""
    if not tag_exists(tag_id):
        return
    ensure_schema()
    mw.col.db.execute(
        "INSERT OR IGNORE INTO ft_failure_tags(failure_id, tag_id) VALUES (?, ?)",
        failure_id, tag_id
    )
    mw.col.setMod()

def remove_tag_from_failure(failure_id: int, tag_name: str):
    tag_id = get_tag_id(tag_name)
    if tag_id is None:
        return
    ensure_schema()
    mw.col.db.execute(
        "DELETE FROM ft_failure_tags WHERE failure_id = ? AND tag_id = ?",
        failure_id, tag_id
    )
    mw.col.setMod()

def tags_for_failure(failure_id: int) -> List[str]:
    ensure_schema()
    return [r[0] for r in mw.col.db.all(
        """SELECT t.name
           FROM ft_failure_tags ft
           JOIN ft_tags t ON t.tag_id = ft.tag_id
           WHERE ft.failure_id = ?
           ORDER BY t.name COLLATE NOCASE""",
        failure_id
    )]

def failures_by_tag(tag_name: str, limit: Optional[int] = None) -> List[int]:
    """Return failure_ids having the given tag name."""
    ensure_schema()
    sql = """
    SELECT ft.failure_id
    FROM ft_failure_tags ft
    JOIN ft_tags t ON t.tag_id = ft.tag_id
    WHERE t.name = ?
    ORDER BY ft.failure_id DESC
    """
    params: list = [tag_name]
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    return [r[0] for r in mw.col.db.all(sql, *params)]