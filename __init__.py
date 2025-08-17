from typing import Literal
from aqt import mw
from aqt.qt import QAction
from .dialogs import CreateFailure, ExploreFailures
from .db import ensure_schema

def _show_explorer():
    ExploreFailures().exec()

def _install_menu():
    action = QAction("Explore Failures", mw)
    action.triggered.connect(_show_explorer)
    mw.form.menuTools.addAction(action)

def _wrap_answer():
    if getattr(mw.reviewer, "_failure_wrap_installed", False):
        return
    ensure_schema()
    original = mw.reviewer._answerCard

    def wrapped(ease: Literal[1,2,3,4]):
        # Intercept only Again(1)/Hard(2)
        if ease in (1,2):
            CreateFailure.prompt(mw.reviewer.card.id, parent=mw)
        return original(ease)

    mw.reviewer._answerCard = wrapped
    mw.reviewer._failure_wrap_installed = True

_install_menu()
_wrap_answer()