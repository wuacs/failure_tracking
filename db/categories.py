# categories_db.py
from aqt import mw
from ..model import DefaultCategory

def ensure_category_table():
    mw.col.db.execute("""
        CREATE TABLE IF NOT EXISTS failure_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE
        )
    """)
    # seed defaults
    for name in DefaultCategory:
        mw.col.db.execute("INSERT OR IGNORE INTO failure_categories(name) VALUES (?)", name.value)

def list_categories(limit: int = None):
    ensure_category_table()
    query = "SELECT name FROM failure_categories ORDER BY name"
    if limit is not None:
        query += " LIMIT ?"
        return [r[0] for r in mw.col.db.all(query, limit)]
    return [r[0] for r in mw.col.db.all(query)]

def add_category(name: str):
    ensure_category_table()
    name = name.strip()
    if not name:
        return False
    mw.col.db.execute("INSERT OR IGNORE INTO failure_categories(name) VALUES (?)", name)
    mw.col.setMod()
    return True

def remove_category(name: str):
    ensure_category_table()
    mw.col.db.execute("DELETE FROM failure_categories WHERE name = ?", name)
    mw.col.setMod()

def validate_category(name: str) -> bool:
    ensure_category_table()
    return bool(mw.col.db.first("SELECT 1 FROM failure_categories WHERE name = ?", name))