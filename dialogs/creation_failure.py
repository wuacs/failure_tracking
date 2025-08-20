from typing import Dict, cast
from aqt import QComboBox, QListWidgetItem, QTextEdit, QWidget, mw, QListWidget, QDialog, QPushButton
from ..db import insert_failure, list_tags
from ..ui import Ui_CreateFailure
from ..model import FailureTag
from PyQt6.QtCore import Qt, QTimer
from .utils.latex import render_latex_to_svg, process_latex_in_text
from .utils.markdown import simple_markdown_to_html

class CreateFailure(QDialog):
    required = [
        "failure_description_text","save_failure_button","cancel_failure_button",
        "tags_combobox","tags_list","add_tag_button",
    ]

    def __init__(self, card_id:int, parent=None):
        super().__init__(parent or mw)
        self.ui = Ui_CreateFailure(); self.ui.setupUi(self)
        self.card_id = card_id
        self.widgets: Dict[str, QWidget] = {n: getattr(self.ui, n) for n in self.required}
                
        self._setup_markdown_preview()
        self._hide_unused_widgets()
        self._setup_tags(); self._setup_save_button(); self._setup_cancel_button()

    def _setup_markdown_preview(self):
        """Set up markdown preview with LaTeX support"""
        if hasattr(self.ui, 'failure_description_preview'):
            # The preview is already a QTextEdit in the UI file
            self.preview_widget = cast(QTextEdit, self.ui.failure_description_preview)
            self.preview_widget.setReadOnly(True)
            self.preview_widget.setPlainText("Preview will appear here...")
            
            # Add live preview update
            self._debounce = QTimer(self)
            self._debounce.setSingleShot(True)
            self._debounce.timeout.connect(self._update_preview)
            
            text_edit = cast(QTextEdit, self.widgets["failure_description_text"])
            text_edit.textChanged.connect(lambda: self._debounce.start(500))
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

    
    def _hide_unused_widgets(self):
        """Hide unused widgets"""
        # Hide some buttons but keep LaTeX button for inserting syntax
        if hasattr(self.ui, 'show_description_preview'):
            self.ui.show_description_preview.hide()

    # buttons / tags
    def _setup_save_button(self):
        cast(QPushButton, self.widgets["save_failure_button"]).clicked.connect(self._on_save)
    def _setup_cancel_button(self):
        cast(QPushButton, self.widgets["cancel_failure_button"]).clicked.connect(self.reject)
    def _setup_tags(self):
        combo = cast(QComboBox, self.widgets["tags_combobox"])
        btn = cast(QPushButton, self.widgets["add_tag_button"])
        combo.clear()
        for tag in list_tags():
            combo.addItem(tag.name, tag)
        btn.clicked.connect(self._on_tag_add)

    # actions
    def _on_save(self):
        reason = cast(QTextEdit, self.widgets["failure_description_text"]).toPlainText()
        if not reason.strip():
            from aqt.utils import tooltip; tooltip("Enter a non-empty reason or Cancel.", period=1500); return
        list_widget = cast(QListWidget, self.widgets["tags_list"])
        tag_ids = [list_widget.item(i).data(Qt.ItemDataRole.UserRole).tag_id for i in range(list_widget.count())]
        insert_failure(card_id=self.card_id, tags_ids=tag_ids, reason=reason)
        self.accept()

    def _on_tag_add(self):
        combo = cast(QComboBox, self.widgets["tags_combobox"])
        list_widget = cast(QListWidget, self.widgets["tags_list"])
        sel: FailureTag = combo.currentData()
        if not sel: return
        existing = {list_widget.item(i).data(Qt.ItemDataRole.UserRole).tag_id for i in range(list_widget.count())}
        if sel.tag_id not in existing:
            item = QListWidgetItem(combo.currentText())
            item.setData(Qt.ItemDataRole.UserRole, sel)
            list_widget.addItem(item)

    @classmethod
    def prompt(cls, card_id:int, parent=None)->bool:
        d = cls(card_id, parent); return d.exec() == 1