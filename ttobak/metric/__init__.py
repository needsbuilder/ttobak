"""Readability scoring (KER — Korean Easy-Read rule evaluator)."""
from __future__ import annotations

from ttobak.levels import Level
from ttobak.metric.models import KERReport


def score(easy_text: str, level: Level, source_text: str | None = None) -> KERReport:
    """Score readability of easy_text via KER rules.

    Stub implementation for Phase 1. Task 34 re-implements with real KER rules.
    """
    raise NotImplementedError("score() is implemented in Task 34")
