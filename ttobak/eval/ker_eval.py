from __future__ import annotations

from typing import Callable

from pydantic import BaseModel

from ttobak.levels import Level
from ttobak.metric.models import KERReport


class KEREvalRow(BaseModel):
    pair_id: str
    before_score: float
    after_score: float
    delta: float
    before_violations: int
    after_violations: int
    violation_reduction: int


class KEREvalReport(BaseModel):
    rows: list[KEREvalRow]
    mean_before: float
    mean_after: float
    mean_delta: float
    mean_violation_reduction: float
    n_pairs: int


def run_ker_eval(pairs: list[dict], score_fn: Callable[[str, Level, "str | None"], KERReport]) -> KEREvalReport:
    """Compute before/after K-ER delta over corpus pairs (spec 14.4).

    For each pair, ``score_fn`` is called on the source (before) and the easy
    text (after) at Level.EASY. Reports per-pair delta + violation reduction and
    corpus-level means. ``score_fn`` is injected for determinism.
    """
    rows: list[KEREvalRow] = []
    for pair in pairs:
        before = score_fn(pair["source_text"], Level.EASY, None)
        after = score_fn(pair["easy_text"], Level.EASY, pair["source_text"])
        rows.append(KEREvalRow(
            pair_id=pair["pair_id"], before_score=before.score, after_score=after.score,
            delta=after.score - before.score, before_violations=len(before.violations),
            after_violations=len(after.violations),
            violation_reduction=len(before.violations) - len(after.violations)))

    n = len(rows)
    if n == 0:
        return KEREvalReport(rows=[], mean_before=0.0, mean_after=0.0, mean_delta=0.0,
                             mean_violation_reduction=0.0, n_pairs=0)
    return KEREvalReport(
        rows=rows,
        mean_before=sum(r.before_score for r in rows) / n,
        mean_after=sum(r.after_score for r in rows) / n,
        mean_delta=sum(r.delta for r in rows) / n,
        mean_violation_reduction=sum(r.violation_reduction for r in rows) / n,
        n_pairs=n)
