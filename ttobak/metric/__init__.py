"""K-ER metric module (Phase-1 placeholder stub — replaced by Task 22)."""
from __future__ import annotations

from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation

__all__ = ["score", "KERReport", "Violation"]


def score(easy_text: str, level: Level, source_text: str | None = None) -> KERReport:
    """Trivial placeholder K-ER report (real rubric lands in Task 22)."""
    return KERReport(
        score=100.0,
        level_estimate=int(level == Level.EASY) + 1,
        sub_scores={"rule": 100.0},
        violations=[],
    )
