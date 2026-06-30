"""Semantic fidelity verification against source (NLI, slot tracking, drift detection)."""
from __future__ import annotations

from datetime import date

from ttobak.ir import Document
from ttobak.fidelity.models import FidelityReport


def verify(source: Document, easy_text: str, ref_date: date) -> FidelityReport:
    """Verify fidelity of easy_text against source.

    Stub implementation for Phase 1. Task 34 re-implements with real NLI/slot tracking.
    """
    raise NotImplementedError("verify() is implemented in Task 34")
