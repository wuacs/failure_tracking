from typing import Optional
from aqt import mw
from aqt.qt import QDialog, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout
from .. import db  # relative import to db module

class CreateFailure(QDialog):
    def __init__(self, card_id: int, parent=None, require_reason=True):
        super().__init__(parent or mw)
        self.card_id = card_id
        self.require_reason = require_reason
        self.setWindowTitle(f"Log failure (Card {card_id})")
        self.resize(380, 260)

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Reason / notes:"))
        self.text = QTextEdit()
        layout.addWidget(self.text)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("Save & Continue")
        self.cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(self.save_btn)
        btn_row.addWidget(self.cancel_btn)
        layout.addLayout(btn_row)

        self.save_btn.clicked.connect(self._on_save)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_save(self):
        reason = self.text.toPlainText().strip()
        if self.require_reason and not reason:
            # lightweight feedback; keep import local to avoid cycles
            from aqt.utils import tooltip
            tooltip("Enter a reason or Cancel.", period=1500)
            return
        if reason:
            db.insert_failure(self.card_id, reason)
        self.accept()

    @classmethod
    def prompt(cls, card_id: int, parent=None, require_reason=True) -> bool:
        d = cls(card_id, parent, require_reason=require_reason)
        return d.exec() == 1