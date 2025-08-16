"""
Contains all persistence-related functionality, including database access and storage.
"""
import time
from aqt import mw

TABLE_SQL = """
CREATE TABLE IF NOT EXISTS failures (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    created_at INTEGER NOT NULL
)
"""
INDEX_SQL = "CREATE INDEX IF NOT EXISTS idx_failures_card_id ON failures(card_id)"

def ensure_schema():
    db = mw.col.db
    db.execute(TABLE_SQL)
    db.execute(INDEX_SQL)

def ensure_cateogory_table():
    mw.col.db.execute("""
        CREATE TABLE IF NOT EXISTS failure_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    for name in ("slip", "wording_unclear", "n/a"):
        mw.col.db.execute("INSERT OR IGNORE INTO failure_categories (name) VALUES (?)", name)

def insert_failure(card_id: int, reason: str):
    if not card_id:
        return
    ensure_schema()
    mw.col.db.execute(
        "INSERT INTO failures(card_id, reason, created_at) VALUES (?,?,?)",
        card_id, reason, int(time.time()),
    )
    mw.col.setMod()

def recent_failures(limit=10):
    ensure_schema()
    return mw.col.db.all(
        "SELECT id, card_id, reason, created_at FROM failures ORDER BY id DESC LIMIT ?",
        limit,
    )