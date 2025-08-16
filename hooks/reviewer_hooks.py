"""
Hooks for the Anki reviewer, allowing customization of the review process.

For now it allows:

1. Intercepting a failed card (Again/Hard) and load failure creation dialog.
"""

from typing import Optional
from aqt import mw
from anki.cards import Card
from aqt.reviewer import Reviewer
from ..dialogs import CreateFailure

INTERCEPT_EASES = {1, 2}  # could load from config later
_ORIG_ATTR = "_orig_answerCard_for_failures"

def get_reviewer_card_id() -> int:
    r: Optional[Reviewer] = getattr(mw, "reviewer", None)
    return r.card.id if r and r.card else 0

def _intercept_answer(ease: int):
    if ease not in INTERCEPT_EASES:
        return getattr(mw.reviewer, _ORIG_ATTR)(ease)

    card: Card = mw.reviewer.card
    if not card:
        return getattr(mw.reviewer, _ORIG_ATTR)(ease)

    if CreateFailure.prompt(card.id, mw):
        getattr(mw.reviewer, _ORIG_ATTR)(ease)
    # else: canceled, stay on card

def install():
    if not hasattr(mw.reviewer, _ORIG_ATTR):
        mw.reviewer.__dict__[_ORIG_ATTR] = mw.reviewer._answerCard
        mw.reviewer._answerCard = _intercept_answer