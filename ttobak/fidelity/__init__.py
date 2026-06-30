"""Ttobak Fidelity gate: slot extraction, normalization, verification, routing.

Public API: ``verify(source, easy_text, ref_date) -> FidelityReport`` (spec 6.2).
Deterministic exact-match path + NegationGuard form the MVP. Semantic NLI
(kf-deberta) is STRETCH and gated behind ``use_nli`` (default False) so it never
blocks the MVP gate.
"""
from __future__ import annotations

from datetime import date

from ttobak.fidelity.extract import extract_slots
from ttobak.fidelity.models import FidelityReport, Slot, SlotType
from ttobak.fidelity.negation_guard import check_negation_flip
from ttobak.fidelity.router import route
from ttobak.fidelity.verify_slots import verify_high_slots
from ttobak.ir import Document

__all__ = ["verify", "FidelityReport", "Slot", "SlotType"]


def verify(source: Document, easy_text: str, ref_date: date,
           *, rounding_allowlist: set[str] | None = None,
           use_nli: bool = False) -> FidelityReport:
    """Verify that the easy text preserves all preservation-required facts.

    Pipeline (spec 6.2): extract typed slots -> exact-match verify HIGH slots ->
    NegationGuard polarity check -> route to PASS / REVISE / HUMAN_REVIEW.
    ``use_nli`` (semantic NLI) is a STRETCH flag, OFF by default.
    """
    slots = extract_slots(source, ref_date)
    failed = verify_high_slots(slots, easy_text, ref_date, rounding_allowlist=rounding_allowlist)
    negation_flips = check_negation_flip(source.text(), easy_text)
    nli_contradictions: list[str] = []
    if use_nli:  # pragma: no cover - STRETCH, gated off in MVP/tests
        nli_contradictions = _run_nli(source.text(), easy_text)

    verdict = route(
        failed_slots=failed,
        negation_flips=negation_flips,
        nli_contradictions=nli_contradictions,
        extraction_low_confidence=_low_confidence(source),
    )

    return FidelityReport(
        slots=slots,
        verdict=verdict,
        exact_fail_count=len(failed),
        nli_contradictions=nli_contradictions,
        drift_flags=negation_flips,
        failed_slots=failed,
    )


def _low_confidence(source: Document) -> bool:
    """Source extraction confidence below 0.5 in any block triggers human review."""
    return any(block.confidence < 0.5 for block in source.blocks)


def _run_nli(source_text: str, easy_text: str) -> list[str]:  # pragma: no cover
    """STRETCH: kf-deberta cross-NLI contradiction detection (best-effort)."""
    try:
        from ttobak.fidelity.nli import detect_contradictions  # type: ignore
    except ImportError:
        return []
    return detect_contradictions(source_text, easy_text)
