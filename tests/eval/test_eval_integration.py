from datetime import date
from pathlib import Path

from ttobak.common import Severity
from ttobak.eval.corpus import load_corpus
from ttobak.eval.distortion_bench import DistortionType, generate_distortions, run_distortion_bench
from ttobak.eval.ker_eval import run_ker_eval
from ttobak.fidelity import verify
from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation

CORPUS = Path(__file__).resolve().parents[2] / "corpus"
REF = date(2026, 7, 1)


def score_fn(easy_text: str, level: Level, source_text: str | None = None) -> KERReport:
    is_source = source_text is None
    sc = 45.0 if is_source else 80.0
    n_viol = 5 if is_source else 1
    return KERReport(score=sc, level_estimate=2, sub_scores={"rule": sc},
                     violations=[Violation(rule="long_sentence", span="…", severity=Severity.MED, suggestion="문장을 나누세요.") for _ in range(n_viol)])


def test_ker_eval_over_real_corpus_shows_positive_delta():
    pairs = [p.model_dump() for p in load_corpus(CORPUS / "pairs.jsonl")]
    report = run_ker_eval(pairs, score_fn)
    assert report.n_pairs >= 1
    assert report.mean_delta > 0


# Distortion types the deterministic MVP gate is NOT responsible for (documented
# out-of-scope): entity substitution and hallucinated-entity injection require
# NER / source-grounding the MVP gate does not implement. Asserting these would
# encode a capability we honestly do not claim.
_OUT_OF_SCOPE = {DistortionType.ENTITY_SWAP.value, DistortionType.HALLUCINATED_ENTITY.value}


def test_distortion_bench_over_real_corpus_real_gate():
    """Run the REAL fidelity gate over the shipped corpus (wiring + honest contract).

    Unlike the literal-marker STUB in ``test_distortion_bench.py``, this injects
    ``ttobak.fidelity.verify`` over every shipped gold pair and asserts the two
    properties that must hold for the corpus to be trustworthy:

      * ``clean_fp_rate == 0`` — the gate never false-flags a faithful gold pair
        (regression guard for the whole corpus; every shipped easy_text PASSes),
      * per-type recall ``== 1.0`` for every distortion type the gate handles.

    ``entity_swap`` / ``hallucinated_entity`` are documented out-of-scope and are
    deliberately not asserted (see ``_OUT_OF_SCOPE`` and the dataset card).
    """
    pairs = load_corpus(CORPUS / "pairs.jsonl")
    all_cases = []
    for i, p in enumerate(pairs):
        all_cases.extend(generate_distortions(p.source_text, p.easy_text, ref_date=REF, seed=i))
    assert any(c.distortion_type == DistortionType.CLEAN for c in all_cases)
    assert sum(1 for c in all_cases if not c.is_clean) >= 5

    res = run_distortion_bench(all_cases, verify, ref_date=REF)
    assert res.clean_fp_rate == 0.0, "real gate false-flagged a faithful gold clean control"
    handled = {d: r for d, r in res.per_type_recall.items() if d not in _OUT_OF_SCOPE}
    assert handled, "no handled distortion type was realized over the corpus"
    for dtype, recall in handled.items():
        assert recall == 1.0, f"real gate missed handled distortion {dtype}: {res.per_type_recall}"
