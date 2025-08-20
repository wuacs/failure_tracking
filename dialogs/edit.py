from typing import Dict, cast
from aqt import QDialog, QPushButton, QTextEdit, QWidget, mw
from ..db import edit_failure
from ..ui import Ui_EditFailure
from ..model import CardFailure
from PyQt6.QtCore import QTimer
from .utils.latex import process_latex_in_text
from .utils.markdown import simple_markdown_to_html

class EditFailure(QDialog):
    required = [
        "failure_description_text", "save_failure_button", "cancel_failure_button"
    ]

    def __init__(self, failure: CardFailure, parent=None):
        super().__init__(parent or mw)
        self.ui = Ui_EditFailure()
        self.ui.setupUi(self)
        self.failure = failure
        print("DEBUG,", self.failure.reason)
        self.widgets: Dict[str, QWidget] = {n: getattr(self.ui, n) for n in self.required}
        self._setup_markdown_preview()
        self._populate_fields()
        self._setup_buttons()

    def _setup_markdown_preview(self):
        """Set up markdown preview with LaTeX support"""
        if hasattr(self.ui, 'failure_description_preview'):
            self.preview_widget = cast(QTextEdit, self.ui.failure_description_preview)
            self.preview_widget.setReadOnly(True)
            self.preview_widget.setPlainText("Preview will appear here...")
            # Add live preview update
            self._debounce = QTimer(self)
            self._debounce.setSingleShot(True)
            self._debounce.timeout.connect(self._update_preview)
            text_edit = cast(QTextEdit, self.widgets["failure_description_text"])
            text_edit.textChanged.connect(lambda: self._debounce.start(500))

    def _populate_fields(self):
        """Fill the dialog with existing failure data"""
        text_edit = cast(QTextEdit, self.widgets["failure_description_text"])
        text_edit.setPlainText(self.failure.reason)
        self._update_preview()  # Initial preview

    def _update_preview(self):
        """Convert markdown with LaTeX to rich text"""
        if not hasattr(self, 'preview_widget'):
            return
            
        text = cast(QTextEdit, self.widgets["failure_description_text"]).toPlainText()
        if not text.strip():
            self.preview_widget.setPlainText("Preview will appear here...")
            return
        
        # First process LaTeX
        text = process_latex_in_text(text)
        
        # Then apply markdown formatting
        html = simple_markdown_to_html(text)
        self.preview_widget.setHtml(html)

    def _setup_buttons(self):
        """Connect button signals"""
        save_btn = cast(QPushButton, self.widgets["save_failure_button"])
        cancel_btn = cast(QPushButton, self.widgets["cancel_failure_button"])
        
        save_btn.clicked.connect(self._on_save)
        cancel_btn.clicked.connect(self.reject)

    def _on_save(self):
        """Save the edited failure"""
        reason = cast(QTextEdit, self.widgets["failure_description_text"]).toPlainText()
        if not reason.strip():
            from aqt.utils import tooltip
            tooltip("Enter a non-empty reason or Cancel.", period=1500)
            return
        
        success = edit_failure(
            failure_id=self.failure.failure_id,
            card_id=self.failure.card_id,
            reason=reason
        )
        
        if success:
            self.accept()
        else:
            from aqt.utils import tooltip
            tooltip("Failed to save changes.", period=1500)

    @classmethod
    def prompt(cls, failure: CardFailure, parent=None) -> bool:
        """Show the edit dialog and return whether changes were saved"""
        dialog = cls(failure, parent)
        return dialog.exec() == 1