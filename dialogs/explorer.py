from typing import Dict, List, Optional, cast
from aqt import QComboBox, QDialog, QPushButton, QWidget, mw, QDateTime, QDateEdit, QTimeZone, QTableView
from ..db import failures_filtered, list_tags
from ..model import CardFailure, CardFailureTableModel, FailureTag
from ..ui import Ui_FailureExplorer
required = ["edit_selected_failure", "delete_selected_failure", 
            "failure_table", "deck_filter_combobox", "tag_filter_combobox",
            "filter_from_date", "filter_to_date", "search_failures_button"]
ALL_ID = - 1
class ExploreFailures(QDialog):
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
        # retrieve filters
        failure_table = cast(QTableView, self.widgets["failure_table"])
        deck: QComboBox = cast(QComboBox, self.widgets["deck_filter_combobox"])
        tag: QComboBox = cast(QComboBox, self.widgets["tag_filter_combobox"])
        from_date_qt: QDateTime = cast(QDateTime, self.widgets["filter_from_date"])
        to_date_qt: QDateTime = cast(QDateTime, self.widgets["filter_to_date"])
        deck_id: Optional[int] = deck.currentData() if deck.currentData() != ALL_ID else None
        tag_id: Optional[int] = tag.currentData() if tag.currentData() != ALL_ID else None
        from_date: str = from_date_qt.toUTC().toPyDateTime().strftime("%Y-%m-%dT%H:%M:%S%z")
        to_date: str = to_date_qt.toUTC().toPyDateTime().strftime("%Y-%m-%dT%H:%M:%S%z")
        failures: list[CardFailure] = failures_filtered(
            deck_id=deck_id,
            tag_id=tag_id,
            interval_iso8601={"from": from_date, "to": to_date}
        )
        failure_table.setModel(CardFailureTableModel(failures))
    def _set_search_button(self):
        search_button = cast(QPushButton, self.widgets["search_failures_button"])
        search_button.clicked.connect(self._on_search)
    def _set_tag_filter(self):
        tag_combobox = cast(QComboBox, self.widgets["tag_filter_combobox"])
        tag_combobox.addItem("All Tags", userData=ALL_ID)
        tags: List[FailureTag] = list_tags()
        for tag in tags:
            tag_combobox.addItem(tag.name, userData=tag.tag_id)
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.ui = Ui_FailureExplorer()
        self.ui.setupUi(self)
        self.widgets: Dict[str, QWidget] = {}
        for name in required:
            widget = self.findChild(QWidget, name)
            if widget:
                self.widgets[name] = widget
            else:
                raise ValueError(f"Missing required widget: {name}, explorer view could not load.")
        self._set_time_filter()
        self._set_deck_filter()
        self._set_tag_filter()
        self._set_search_button()