# __init__.py
import os
import sys
from aqt import QDialog, QVBoxLayout, QWebEngineView, mw, gui_hooks
from typing import Literal
from aqt.qt import QAction
from .dialogs import CreateFailure, ExploreFailures
from .db import ensure_schema

def _setup_libs():
    """Add the bundled libraries to Python path"""
    libs_dir = os.path.join(os.path.dirname(__file__), 'libs')
    if os.path.exists(libs_dir) and libs_dir not in sys.path:
        sys.path.insert(0, libs_dir)
        print(f"DEBUG: Added {libs_dir} to Python path")

def _show_explorer():
    ExploreFailures().exec()

def _install_menu():
    action = QAction("Explore Failures", mw)
    action.triggered.connect(_show_explorer)
    mw.form.menuTools.addAction(action)

def _wrap_answer():
    if getattr(mw.reviewer, "_failure_wrap_installed", False):
        return
    original = mw.reviewer._answerCard
    def wrapped(ease: Literal[1,2,3,4]):
        if ease in (1,2):
            ok = CreateFailure.prompt(card_id=mw.reviewer.card.id)
            if not ok:
                return
        return original(ease)
    mw.reviewer._answerCard = wrapped
    mw.reviewer._failure_wrap_installed = True

def _init_after_profile():
    ensure_schema()
    _install_menu()
    _wrap_answer()
    _setup_libs()

gui_hooks.profile_did_open.append(lambda _ = None: _init_after_profile())