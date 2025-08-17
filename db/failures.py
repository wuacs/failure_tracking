from typing import Dict, List, Literal, Optional
from aqt import mw
from ..model import CardFailure
from .tags import assign_tag_to_failure
from datetime import datetime, timezone

def ensure_schema():
    query = """
    CREATE TABLE IF NOT EXISTS failures (
    failure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL)""" #date is stored as ISO8601 string no microseconds
    mw.col.db.execute(query)
    mw.col.db.execute("CREATE INDEX IF NOT EXISTS idx_failures_created_at ON failures(created_at)")
    mw.col.db.execute("CREATE INDEX IF NOT EXISTS idx_failures_card_id ON failures(card_id)")

def _utc_now_iso_seconds() -> str:
    # 2025-08-17T14:22:05+00:00 (no microseconds)
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()

def insert_failure(card_id: int, tags_ids: Optional[List[int]], reason: str) -> Optional[int]:
    """
    Returns the failure added ID if insertion was successful, None otherwise.
    """
    ensure_schema()
    if not reason.strip():
        return None
    mw.col.db.execute(
        "INSERT INTO failures(card_id, reason, created_at) VALUES (?,?,?)",
        card_id, reason.strip(), _utc_now_iso_seconds()
    )
    failure_id = mw.col.db.scalar("SELECT last_insert_rowid()")
    for tag_id in tags_ids or []:
        assign_tag_to_failure(failure_id, tag_id)
    mw.col.setMod()
    return failure_id

def failures_filtered(
    deck_id: Optional[int] = None,
    card_id: Optional[int] = None,
    tag_id: Optional[int] = None,
    limit: Optional[int] = None,
    interval_iso8601: Optional[Dict[Literal["from", "to"], str]] = None
) -> list[CardFailure]:
    ensure_schema()
    sql = """
    SELECT f.failure_id, f.card_id, f.reason, f.created_at
    FROM failures f
    JOIN cards c ON c.id = f.card_id
    """
    where = []
    params: list = []
    if deck_id is not None:
        where.append("c.did = ?")
        params.append(deck_id)
    if card_id is not None:
        where.append("f.card_id = ?")
        params.append(card_id)
    if interval_iso8601  is not None:
        where.append("f.created_at BETWEEN ? AND ?")
        params.append(interval_iso8601["from"])
        params.append(interval_iso8601["to"])
    if tag_id is not None:
        where.append(" ? IN (SELECT tag_id FROM failure_tags WHERE failure_id = f.failure_id)")
        params.append(tag_id)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY f.failure_id DESC"
    if limit is not None:
        sql += " LIMIT ?"
        params.append(limit)
    rows = mw.col.db.all(sql, *params)
    return [CardFailure(
        failure_id=r[0],
        card_id=r[1],
        reason=r[2],
        created_at=datetime.fromisoformat(r[3]).astimezone(timezone.utc),
    ) for r in rows]