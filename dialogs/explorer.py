from aqt import QDialog, mw


class ExploreFailures(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent or mw)
        self.setWindowTitle("Failure Explorer")
        self.resize(800, 600)
        
