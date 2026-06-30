"""K-ER metric module — rule-based rubric (Task 22).

규칙 기반 루브릭, 경험적 검증 아님. The score is the mean of 12 sub-rule scores
(each 0–100, higher = easier to read). Level estimate: ≥80 → 1, ≥60 → 2, else 3.
"""
from __future__ import annotations

from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation

__all__ = ["score", "KERReport", "Violation"]


def score(easy_text: str, level: Level, source_text: str | None = None) -> KERReport:
    """Compute a K-ER readability report for *easy_text*.

    Tokenizes once via kiwipiepy (isolated in ttobak.metric.tokenize), runs all
    twelve rules in ALL_RULES, returns the per-rule sub_scores and aggregated
    score (mean) plus the Violation checklist.

    규칙 기반 루브릭, 경험적 검증 아님.
    """
    from ttobak.metric.tokenize import tokenize
    from ttobak.metric.rules import ALL_RULES

    tokens = tokenize(easy_text)

    sub_scores: dict[str, float] = {}
    all_violations: list[Violation] = []

    for name, rule_fn in ALL_RULES:
        result = rule_fn(easy_text, tokens)
        sub_scores[name] = result.sub_score
        all_violations.extend(result.violations)

    mean_score = sum(sub_scores.values()) / len(sub_scores) if sub_scores else 0.0

    if mean_score >= 80.0:
        level_estimate = 1
    elif mean_score >= 60.0:
        level_estimate = 2
    else:
        level_estimate = 3

    return KERReport(
        score=mean_score,
        level_estimate=level_estimate,
        sub_scores=sub_scores,
        violations=all_violations,
    )
