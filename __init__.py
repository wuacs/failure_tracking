import time
from typing import Optional
from aqt import QLayout, mw
from aqt.qt import QAction, QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout
from aqt.reviewer import Reviewer
from aqt.utils import tooltip
from anki.cards import Card

# ---- DB (in collection) ----

_attr_prefix = "_failure"

def ensure_table():
    """Creates the tables if they don't exist"""
    db = mw.col.db
    db.execute("""
        CREATE TABLE IF NOT EXISTS failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_id INTEGER NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
            reason TEXT NOT NULL,
            created_at INTEGER NOT NULL
        )
    """)
    db.execute("CREATE INDEX IF NOT EXISTS idx_failures_card_id ON failures(card_id)")

def log_failure(card_id: int, reason: str):
    if not card_id:
        return
    ensure_table()
    mw.col.db.execute(
        "INSERT INTO failures(card_id, reason, created_at) VALUES (?,?,?)",
        card_id,
        reason,
        int(time.time()),
    )
    # Mark collection modified so it eventually saves
    mw.col.setMod()

# ---- Dialog ----

class FailureDialog(QDialog):
    def __init__(self, card_id, parent=None):
        super().__init__(parent or mw)
        self.card_id = card_id
        self.setWindowTitle(f"Log failure (Card {card_id})")
        self.resize(360, 240)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reason / notes:"))
        self.text = QTextEdit()
        layout.addWidget(self.text)
        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save & Exit")
        self.cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self.save_btn.clicked.connect(self.save_and_close)
        self.cancel_btn.clicked.connect(self.reject)

    def save_and_close(self):
        reason = self.text.toPlainText().strip()
        if reason:
            log_failure(self.card_id, reason)
        self.close()

def current_card_id():
    r: Optional[Reviewer] = getattr(mw, "reviewer", None)
    return r.card.id if r and r.card else 0

def show_failure_dialog():
    existing: Optional[FailureDialog] = getattr(mw, _attr_prefix + "_dialog", None)
    if existing and existing.isVisible():
        existing.raise_(); existing.activateWindow(); return
    d = FailureDialog(current_card_id(), mw)
    setattr(mw, _attr_prefix + "_dialog", d)
    d.show()


if not hasattr(mw.reviewer, "_orig_answerCard_for_failures"):
    # Keep original _answerCard method
    mw.reviewer._orig_answerCard_for_failures = mw.reviewer._answerCard

    def _failure_intercept_answer(ease: int):
        # Only intercept Again(1) / Hard(2) (TO-DO MAKE THIS DYNAMIC, I.E MAKE THE USER CONFIGURE THIS)
        if ease not in (1, 2):
            return mw.reviewer._orig_answerCard_for_failures(ease)

        card: Card = mw.reviewer.card
        if not card:
            return mw.reviewer._orig_answerCard_for_failures(ease)

        # Build blocking dialog
        dialog = FailureDialog(card.id, mw)
        if dialog.exec() == 1:  # 1 means user clicked Save & Exit
            mw.reviewer._orig_answerCard_for_failures(ease)
        else:
            # Rejected: do nothing; user stays on same card
            pass

    mw.reviewer._answerCard = _failure_intercept_answer