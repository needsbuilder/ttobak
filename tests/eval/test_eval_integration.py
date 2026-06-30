from datetime import date
from pathlib import Path

from ttobak.common import Severity, Verdict
from ttobak.eval.corpus import load_corpus
from ttobak.eval.distortion_bench import DistortionType, generate_distortions, run_distortion_bench
from ttobak.eval.ker_eval import run_ker_eval
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Document
from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation

CORPUS = Path(__file__).resolve().parents[2] / "corpus"


def score_fn(easy_text: str, level: Level, source_text: str | None = None) -> KERReport:
    is_source = source_text is None
    sc = 45.0 if is_source else 80.0
    n_viol = 5 if is_source else 1
    return KERReport(score=sc, level_estimate=2, sub_scores={"rule": sc},
                     violations=[Violation(rule="long_sentence", span="…", severity=Severity.MED, suggestion="문장을 나누세요.") for _ in range(n_viol)])


_MARKERS = ("3,000원", "129,540", "7월 7일", "전에", "이하", "송파구청", "국민건강보험공단")


def verify_fn(source: Document, easy_text: str, ref_date: date) -> FidelityReport:
    """STUB gate (literal markers). Exercises corpus->bench WIRING, not the real
    gate's recall. The real gate is scored in
    ``tests/eval/test_distortion_bench_real_gate.py``."""
    verdict = Verdict.HUMAN_REVIEW if any(m in easy_text for m in _MARKERS) else Verdict.PASS
    return FidelityReport(slots=[], verdict=verdict)


def test_ker_eval_over_real_corpus_shows_positive_delta():
    pairs = [p.model_dump() for p in load_corpus(CORPUS / "pairs.jsonl")]
    report = run_ker_eval(pairs, score_fn)
    assert report.n_pairs >= 1
    assert report.mean_delta > 0


def test_distortion_bench_over_real_corpus_catches_distortions():
    pairs = load_corpus(CORPUS / "pairs.jsonl")
    all_cases = []
    for p in pairs:
        all_cases.extend(generate_distortions(p.source_text, p.easy_text, ref_date=date(2026, 7, 1)))
    assert any(c.distortion_type == DistortionType.CLEAN for c in all_cases)
    assert sum(1 for c in all_cases if not c.is_clean) >= 5

    res = run_distortion_bench(all_cases, verify_fn, ref_date=date(2026, 7, 1))
    assert res.overall_recall == 1.0
    assert res.clean_fp_rate == 0.0
    assert res.pass_residual_distortion_rate == 0.0
