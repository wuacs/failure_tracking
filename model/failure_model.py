from typing import List, Optional
from PyQt6.QtCore import Qt, QAbstractItemModel, QModelIndex
from aqt import QAbstractTableModel

from .failure import CardFailure

class CardFailureTableModel(QAbstractTableModel):
    def __init__(self, failures, parent=None):
        super().__init__(parent)
        self._failures = failures
        # map column → (header, attribute name)
        self._columns = [
            ("Failure ID", "failure_id"),
            ("Card ID", "card_id"),
            ("Reason", "reason"),
            ("Created At", "created_at"),
        ]

    def rowCount(self, parent=None):
        return len(self._failures)

    def columnCount(self, parent=None):
        return len(self._columns)

    def get_failure_at_row(self, row: int) -> Optional[CardFailure]:
        if 0 <= row < len(self._failures):
            return self._failures[row]
        return None

    def update_row(self, row: int, failure: CardFailure):
        if 0 <= row < len(self._failures):
            self._failures[row] = failure
            self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
        else:
            print("Invalid row index")

    def remove_row(self, row: int):
        if 0 <= row < len(self._failures):
            self._failures.pop(row)
            self.dataChanged.emit(self.index(row, 0), self.index(row, self.columnCount() - 1))
        else:
            print("Invalid row index")

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or role != Qt.ItemDataRole.DisplayRole:
            return None
        obj = self._failures[index.row()]
        attr_name = self._columns[index.column()][1]
        return getattr(obj, attr_name)

    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self._columns[section][0]
        return None