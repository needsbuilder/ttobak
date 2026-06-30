from ttobak.common import Severity
from ttobak.eval.ker_eval import KEREvalReport, KEREvalRow, run_ker_eval
from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation


def _report(score: float, n_violations: int) -> KERReport:
    violations = [Violation(rule="long_sentence", span="…", severity=Severity.MED, suggestion="문장을 나누세요.") for _ in range(n_violations)]
    return KERReport(score=score, level_estimate=2, sub_scores={"rule": score}, violations=violations)


def make_score_fn(table):
    def score_fn(easy_text: str, level: Level, source_text: str | None = None):
        return _report(*table[easy_text])
    return score_fn


PAIRS = [
    {"pair_id": "p1", "source_text": "원문1 매우 어렵고 긴 문장입니다.", "easy_text": "쉬운1 짧아요."},
    {"pair_id": "p2", "source_text": "원문2 한자어가 많은 공문입니다.", "easy_text": "쉬운2 쉬워요."},
]
TABLE = {
    "원문1 매우 어렵고 긴 문장입니다.": (40.0, 6),
    "쉬운1 짧아요.": (82.0, 1),
    "원문2 한자어가 많은 공문입니다.": (50.0, 4),
    "쉬운2 쉬워요.": (80.0, 0),
}


def test_runs_and_returns_report():
    res = run_ker_eval(PAIRS, make_score_fn(TABLE))
    assert isinstance(res, KEREvalReport)
    assert res.n_pairs == 2
    assert all(isinstance(r, KEREvalRow) for r in res.rows)


def test_per_pair_delta_and_violation_reduction():
    by_id = {r.pair_id: r for r in run_ker_eval(PAIRS, make_score_fn(TABLE)).rows}
    assert by_id["p1"].before_score == 40.0 and by_id["p1"].after_score == 82.0
    assert by_id["p1"].delta == 42.0
    assert by_id["p1"].before_violations == 6 and by_id["p1"].after_violations == 1
    assert by_id["p1"].violation_reduction == 5
    assert by_id["p2"].delta == 30.0 and by_id["p2"].violation_reduction == 4


def test_corpus_level_means():
    res = run_ker_eval(PAIRS, make_score_fn(TABLE))
    assert res.mean_before == 45.0 and res.mean_after == 81.0
    assert res.mean_delta == 36.0 and res.mean_violation_reduction == 4.5


def test_empty_pairs_gives_zero_means():
    res = run_ker_eval([], make_score_fn(TABLE))
    assert res.n_pairs == 0 and res.mean_before == 0.0 and res.mean_delta == 0.0 and res.rows == []
