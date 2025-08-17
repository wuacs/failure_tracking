from typing import Optional
from aqt import mw

def _add_limit(query: str, limit: Optional[int] = None) -> tuple[str, list]:
    if limit is not None:
        query += " LIMIT ?"
    return query, [limit] if limit is not None else []

def execute_select_query(query: str, limit: Optional[int] = None) -> list:
    query, params = _add_limit(query, limit)
    return mw.col.db.all(query, *params)