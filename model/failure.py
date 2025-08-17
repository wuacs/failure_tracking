from datetime import datetime, timezone

class CardFailure:
    def __init__(self, failure_id: int, card_id: int, reason: str, created_at: datetime):
        self.failure_id = failure_id
        self.card_id = card_id
        self.reason = reason
        dt = created_at
        utc_dt = dt.astimezone(timezone.utc)
        self.created_at = utc_dt.isoformat()  # Store as ISO8601 string
