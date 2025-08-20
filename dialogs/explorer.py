from typing import Dict, List, cast
from aqt import QComboBox, QDialog, QMessageBox, QModelIndex, QPushButton, QTextEdit, QVBoxLayout, QWidget, mw, QDateTime, QDateEdit, QTimeZone, QTableView
from ..db import failures_filtered, list_tags, delete_failure
from ..model import CardFailure, CardFailureTableModel, FailureTag
from ..ui import Ui_FailureExplorer
from .utils.latex import process_latex_in_text
from .utils.markdown import simple_markdown_to_html
from .edit import EditFailure
from aqt.utils import tooltip, askUser
from aqt.browser.previewer import Previewer
from aqt import dialogs
from anki.cards import Card
from aqt.browser.card_info import CardInfoDialog

ALL_ID = - 1
class ExploreFailures(QDialog):
    required = ["edit_selected_failure", "delete_selected_failure", 
            "failure_table", "deck_filter_combobox", "tag_filter_combobox",
            "filter_from_date", "filter_to_date", "search_failures_button"]
    def _keep_to_ahead(self):
        if self.widgets["filter_from_date"].dateTime() > self.widgets["filter_to_date"].dateTime():
            self.widgets["filter_to_date"].setDateTime(min(self.widgets["filter_from_date"].dateTime().addDays(1), QDateTime.currentDateTime()))
    def _set_time_filter(self):
        now = QDateTime.currentDateTime(QTimeZone.utc())
        from_obj = cast(QDateEdit, self.widgets["filter_from_date"])
        to_obj = cast(QDateEdit, self.widgets["filter_to_date"])
        from_obj.setDateTime(now.addDays(-7))  # Default to 7 days ago
        to_obj.setDateTime(now)
        from_obj.dateTimeChanged.connect(self._keep_to_ahead)
    def _set_deck_filter(self):
        deck_combobox = cast(QComboBox, self.widgets["deck_filter_combobox"])
        deck_combobox.addItem("All Decks", userData=ALL_ID)
        for deck_id in mw.col.decks.all_names_and_ids():
            deck_combobox.addItem(deck_id.name, userData=deck_id.id)
    def _on_search(self):
        table = self.widgets["failure_table"]
        deck: QComboBox = cast(QComboBox, self.widgets["deck_filter_combobox"])
        tag: QComboBox = cast(QComboBox, self.widgets["tag_filter_combobox"])
        deck_id = deck.currentData()
        if deck_id == ALL_ID:
            deck_id = None
        tag_id = tag.currentData()
        if tag_id == ALL_ID:
            tag_id = None
        from_edit = cast(QDateEdit, self.widgets["filter_from_date"])
        to_edit = cast(QDateEdit, self.widgets["filter_to_date"])
        from_dt = from_edit.dateTime().toUTC().toPyDateTime()
        to_dt = to_edit.dateTime().toUTC().toPyDateTime()
        interval = {
            "from": from_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
            "to": to_dt.strftime("%Y-%m-%dT%H:%M:%S+00:00"),
        }
        failures = failures_filtered(deck_id=deck_id, tag_id=tag_id, interval_iso8601=interval)
        table = cast(QTableView, self.widgets["failure_table"])
        self.failures_model = CardFailureTableModel(failures)
        table.setModel(self.failures_model)
        table.doubleClicked.connect(self._on_failure_double_clicked)
    def _on_failure_double_clicked(self, index: QModelIndex):
        """Handle double-click on a failure entry"""
        if index.column() == CardFailureTableModel.COLUMN_MAPPING["card_id"]:
            card: Card = mw.col.get_card( self.failures_model.data(index))
            dlg = QDialog(self)
            dlg.setWindowTitle(f"Card {card.id} Preview")
            lay = QVBoxLayout(dlg)
            box = QTextEdit()
            box.setReadOnly(True)
            box.setHtml(card.a())
            lay.addWidget(box)
            dlg.exec()
        else: 
            preview = QDialog(self)
            layout = QVBoxLayout(preview)
            text = QTextEdit()
            text.setReadOnly(True)
            if index.column() == CardFailureTableModel.COLUMN_MAPPING["reason"]: #fix this magic number
                text.setHtml(simple_markdown_to_html(process_latex_in_text(self.failures_model.data(index))))
            else:
                text.setText(str(self.failures_model.data(index)))
            layout.addWidget(text)
            preview.setWindowTitle("Details")
            preview.exec()
    def _set_search_button(self):
        search_button = cast(QPushButton, self.widgets["search_failures_button"])
        search_button.clicked.connect(self._on_search)
    def _set_tag_filter(self):
        tag_combobox = cast(QComboBox, self.widgets["tag_filter_combobox"])
        tag_combobox.addItem("All Tags", userData=ALL_ID)
        tags: List[FailureTag] = list_tags()
        for tag in tags:
            tag_combobox.addItem(tag.name, userData=tag.tag_id)
    def _on_edit_failure(self):
        """Open the edit dialog for the selected failure"""
        table = cast(QTableView, self.widgets["failure_table"])
        index = table.currentIndex()
        if not index.isValid():
            tooltip("Select a failure to edit.", period=1500); return
        failure: CardFailure = self.failures_model.get_failure_at_row(index.row())
        dialog = EditFailure(failure, parent=self)
        dialog.exec()
        newfailure: CardFailure = failures_filtered(failure_id=failure.failure_id)[0]
        self.failures_model.update_row(index.row(), newfailure)
    def _on_delete_failure(self):
        """Delete the selected failure"""
        table = cast(QTableView, self.widgets["failure_table"])
        index = table.currentIndex()
        if not index.isValid():
            tooltip("Select a failure to delete.", period=1500); return
        failure: CardFailure = self.failures_model.get_failure_at_row(index.row())
         # Use Anki's askUser function instead of QMessageBox
        if askUser(f"Are you sure you want to delete failure {failure.failure_id}?"):
            if delete_failure(failure.failure_id):
                tooltip(f"Failure {failure.failure_id} deleted successfully.", period=1500)
                self.failures_model.remove_row(index.row())
            else:
                tooltip("Failed to delete failure.", period=1500)
    def _set_edit_button(self):
        edit_button = cast(QPushButton, self.widgets["edit_selected_failure"])
        edit_button.clicked.connect(self._on_edit_failure)
    def _set_delete_button(self):
        delete_button = cast(QPushButton, self.widgets["delete_selected_failure"])
        delete_button.clicked.connect(self._on_delete_failure)
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.ui = Ui_FailureExplorer()
        self.ui.setupUi(self)
        self.widgets: Dict[str, QWidget] = {n: getattr(self.ui, n) for n in self.required}
        self._set_time_filter()
        self._set_deck_filter()
        self._set_tag_filter()
        self._set_search_button()
        self._set_edit_button()
        self._set_delete_button()
