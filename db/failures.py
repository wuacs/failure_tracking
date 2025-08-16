from typing import List
from aqt import mw
from ..model import CardFailure
from .utils import execute_select_query
from datetime import datetime, timezone

def ensure_schema():
    query = """
    CREATE TABLE IF NOT EXISTS failures (
    failure_id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    category_id INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL)""" #date is stored as ISO8601 string
    mw.col.db.execute(query)

def insert_failure(card_id: int, category_id: int, reason: str):
    if not card_id:
        return
    ensure_schema()
    mw.col.db.execute(
        "INSERT INTO failures(card_id, category_id, reason, created_at) VALUES (?,?,?,?)",
        card_id, category_id, reason, datetime.now(timezone.utc).isoformat()
    )
    mw.col.setMod()

def recent_failures(limit: int = None) -> List[CardFailure]:
    ensure_schema()
    result = execute_select_query("SELECT failure_id, card_id, reason, category_id, created_at FROM failures ORDER BY failure_id DESC", limit)
    return [CardFailure(failure_id=row[0], card_id=row[1], reason=row[2], category_id=row[3], created_at=row[4]) for row in result]

def get_failures_by_category(category: str, limit: int = None) -> List[CardFailure]:
    ensure_schema()
    query = "SELECT failure_id, card_id, reason, category_id, created_at FROM failures WHERE category_id = ? ORDER BY failure_id DESC"
    return [CardFailure(failure_id=row[0], card_id=row[1], reason=row[2], category_id=row[3], created_at=row[4]) for row in execute_select_query(query, category, limit)]

def get_failures_by_card(card_id: int, limit: int = None) -> List[CardFailure]:
    ensure_schema()
    query = "SELECT failure_id, card_id, reason, category_id, created_at FROM failures WHERE card_id = ? ORDER BY failure_id DESC"
    return [CardFailure(failure_id=row[0], card_id=row[1], reason=row[2], category_id=row[3], created_at=row[4]) for row in execute_select_query(query, card_id, limit)]

def get_failures_by_deck(deck_id: int, limit: int = None) -> List[CardFailure]:
    ensure_schema()
    query = """
    SELECT f.failure_id, f.card_id, f.reason, f.category_id, f.created_at
    FROM failures f
    JOIN cards c ON c.id = f.card_id
    WHERE c.did = ?
    ORDER BY f.failure_id DESC
    """
    return [CardFailure(failure_id=row[0], card_id=row[1], reason=row[2], category_id=row[3], created_at=row[4]) for row in execute_select_query(query, deck_id, limit)]