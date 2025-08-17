from typing import Dict, List, cast
from aqt import QComboBox, QListWidgetItem, QTextEdit, QWidget, mw, QListWidget
from aqt.qt import QDialog, QVBoxLayout, QPushButton, QLabel, QWebEngineView
from ..db import insert_failure, list_tags
from ..ui import Ui_CreateFailure
from ..model import FailureTag
from PyQt6.QtCore import Qt

required = ["failure_description_text", "add_latex_button",
            "save_failure_button", "cancel_failure_button", "tags_combobox",
            "tags_list", "show_description_preview", "add_tag_button"]


class CreateFailure(QDialog):
    MATHJAX_TEMPLATE = """
    <html>
    <head>
        <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
        <script id="MathJax-script" async
        src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js">
        </script>
    </head>
    <body>
        <div id="content">
        {content}
        </div>
    </body>
    </html>
    """
    def _setup_save_button(self):
        save_btn = cast(QPushButton, self.widgets["save_failure_button"])
        save_btn.clicked.connect(self._on_save)
    def _setup_cancel_button(self):
        cancel_btn = cast(QPushButton, self.widgets["cancel_failure_button"])
        cancel_btn.clicked.connect(self.reject)
    def _setup_preview_button(self):
        preview_btn = cast(QPushButton, self.widgets["show_description_preview"])
        preview_btn.clicked.connect(self._on_show_preview)
    def _setup_add_latex_button(self):
        add_latex_btn = cast(QPushButton, self.widgets["add_latex_button"])
        add_latex_btn.clicked.connect(self._on_add_latex)
    def _setup_tags(self):
        tags_combobox = cast(QComboBox, self.widgets["tags_combobox"])
        add_tags_button = cast(QPushButton, self.widgets["add_tag_button"])
        tags: List[FailureTag] = list_tags()
        for tag in tags:
            tags_combobox.addItem(tag.name, tag)
        add_tags_button.clicked.connect(self._on_tag_add)
    def __init__(self, card_id: int, parent=None):
        super().__init__(parent or mw)
        self.card_id = card_id
        self.ui = Ui_CreateFailure()
        self.ui.setupUi(self)
        self.widgets: Dict[str, QWidget] = {}
        for name in required:
            widget = self.findChild(QWidget, name)
            if widget:
                self.widgets[name] = widget
            else:
                raise ValueError(f"Missing required widget: {name}, explorer view could not load.")
        self.setWindowTitle(f"Log failure (Card {card_id})")
        self._setup_add_latex_button()
        self._setup_preview_button()
        self._setup_tags()
        self._setup_save_button()
        self._setup_cancel_button()
    def _on_save(self):
        reason = self.ui.failure_description_text.toPlainText()
        if not reason or not reason.strip():
            # lightweight feedback; keep import local to avoid cycles
            from aqt.utils import tooltip
            tooltip("Enter a non-empty reason or Cancel.", period=1500)
            return
        list_widget = cast(QListWidget, self.widgets["tags_list"])
        tags_ids = [list_widget.item(i).data(Qt.ItemDataRole.UserRole).tag_id for i in range(list_widget.count())]
        insert_failure(card_id=self.card_id, tags_ids=tags_ids, reason=reason)
        self.accept()
    def _on_add_latex(self):
        description: QTextEdit = cast(QTextEdit, self.widgets["failure_description_text"])
        cursor = description.textCursor()
        cursor.insertText(r"\[ \]")
        for _ in range(3):
            cursor.movePosition(cursor.MoveOperation.Left)
        description.setTextCursor(cursor)
    def _on_show_preview(self):
        preview_dialog = QDialog(self)
        preview_dialog.setWindowTitle("Preview")
        layout = QVBoxLayout(preview_dialog)
        content = QWebEngineView()
        content.setHtml(CreateFailure.MATHJAX_TEMPLATE.format(content=self.ui.failure_description_text.toPlainText().strip()))
        layout.addWidget(QLabel("Preview:"))
        layout.addWidget(content)
        preview_dialog.exec()
    def _on_tag_add(self):
        tags_combobox = cast(QComboBox, self.widgets["tags_combobox"])
        tags_list = cast(QListWidget, self.widgets["tags_list"])
        selected_tag: FailureTag = tags_combobox.currentData()
        if selected_tag and selected_tag.tag_id not in [tags_list.item(i).data(Qt.ItemDataRole.UserRole).tag_id for i in range(tags_list.count())]:
            item = QListWidgetItem(tags_combobox.currentText())
            item.setData(Qt.ItemDataRole.UserRole, selected_tag)
            tags_list.addItem(item)
    @classmethod
    def prompt(cls, card_id: int, parent=None) -> bool:
        d = cls(card_id, parent)
        return d.exec() == 1