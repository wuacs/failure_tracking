from datetime import datetime, timezone

class CardFailure:
    def __init__(self, failure_id: int, card_id: int, category_id: int, reason: str):
        self.failure_id = failure_id
        self.card_id = card_id
        self.category_id = category_id
        self.reason = reason
        self.created_at = datetime.now(timezone.utc).timestamp()
