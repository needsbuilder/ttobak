"""Fidelity gate module (Phase-1 placeholder stub — replaced by Task 30)."""
from __future__ import annotations

from datetime import date

from ttobak.common import Verdict
from ttobak.fidelity.models import FidelityReport, Slot
from ttobak.ir import Document

__all__ = ["verify", "FidelityReport", "Slot"]


def verify(source: Document, easy_text: str, ref_date: date) -> FidelityReport:
    """Trivial placeholder Fidelity report — PASS (real gate lands in Task 30)."""
    return FidelityReport(slots=[], verdict=Verdict.PASS)
