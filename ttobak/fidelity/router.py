"""Fidelity router: PASS / REVISE / HUMAN_REVIEW (spec 6.8).

- PASS: every HIGH slot survived, no NLI contradiction, no negation flip.
- REVISE (auto loop): only recoverable exact-match failures (numeric/date/
  money/duration/contact/scope) — re-inject as 'verbatim, no paraphrase' constraints.
- HUMAN_REVIEW: negation/condition polarity flip, NLI contradiction, low
  source-extraction confidence, or a failed semantic slot (eligibility/
  conditional/agency/person/modality) that cannot be safely auto-revised.
"""
from __future__ import annotations

from ttobak.common import Verdict
from ttobak.fidelity.models import Slot, SlotType

_AUTO_RECOVERABLE = {
    SlotType.NUMERIC,
    SlotType.DATE,
    SlotType.MONEY,
    SlotType.DURATION,
    SlotType.CONTACT,
    SlotType.SCOPE,
}


def route(failed_slots: list[Slot], negation_flips: list[str],
          nli_contradictions: list[str], extraction_low_confidence: bool) -> Verdict:
    """Map verification outcomes to a routing verdict per spec 6.8."""
    if negation_flips or nli_contradictions or extraction_low_confidence:
        return Verdict.HUMAN_REVIEW
    if not failed_slots:
        return Verdict.PASS
    if any(s.type not in _AUTO_RECOVERABLE for s in failed_slots):
        return Verdict.HUMAN_REVIEW
    return Verdict.REVISE
