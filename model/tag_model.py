from aqt import QAbstractListModel, QModelIndex, Qt
from .failure_tag import FailureTag
class TagsFailureListModel(QAbstractListModel):
    def __init__(self, tags: list[FailureTag], parent=None):
        super().__init__(parent)
        self._tags: list[FailureTag] = tags

    def rowCount(self, parent=QModelIndex()):
        return len(self._tags)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        tag = self._tags[index.row()]
        if role == Qt.ItemDataRole.DisplayRole:
            return tag.name
        return None
