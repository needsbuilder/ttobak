"""Real-gate distortion bench (M3): injects the ACTUAL ``ttobak.fidelity.verify``.

Unlike ``test_distortion_bench.py`` (which scores a literal-marker STUB to prove
the bench arithmetic) and ``test_eval_integration.py`` (corpus->bench wiring),
this module runs the REAL Fidelity gate over per-distortion ISOLATED minimal
corpora — one faithful (source, easy) pair per distortion type the gate is meant
to handle. It asserts BOTH:

  * per-distortion recall is 1.0 for the handled types (the gate actually flags
    the injected distortion), AND
  * clean_fp_rate == 0.0 (the faithful CLEAN control is never flagged).

This is the test that exposed the original false-negatives: it passes ONLY after
the M1 (date inclusivity) and M2 (eligibility boundary operator) fixes land —
before them, faithful eligibility controls were false-positive flagged (clean_fp
> 0) and inclusivity flips slipped through.
"""
from datetime import date

from ttobak.eval.distortion_bench import (
    DistortionType,
    generate_distortions,
    run_distortion_bench,
)
from ttobak.fidelity import verify

REF = date(2026, 7, 1)

# One faithful (source, easy) pair per distortion type the gate handles. Each
# easy_text is a verbatim faithful copy of source (so the CLEAN control PASSes)
# and contains the distorter's trigger pattern (so the distortion is realized).
_HANDLED_PAIRS: dict[str, tuple[str, str]] = {
    "number_swap": ("보험료는 30,000원입니다.", "보험료는 30,000원입니다."),
    "krw_unit_error": ("지원금은 3억 원입니다.", "지원금은 3억 원입니다."),
    "date_shift": ("신청 기한은 2026년 7월 17일까지입니다.", "신청 기한은 2026년 7월 17일까지입니다."),
    "inclusivity_flip": ("2026년 7월 17일까지 납부하세요.", "2026년 7월 17일까지 납부하세요."),
    "condition_flip": ("만 65세 이상만 신청 가능합니다.", "만 65세 이상만 신청 가능합니다."),
    "range_weaken": ("소득 100만원 미만 가구가 대상입니다.", "소득 100만원 미만 가구가 대상입니다."),
    "negation_drop": ("외국인은 대상에서 제외됩니다.", "외국인은 대상에서 제외됩니다."),
}

# Distortion types whose detection this MVP gate is responsible for. Other
# realized types (e.g. hallucinated_entity) are out of scope and not asserted.
_GATE_HANDLED = {
    DistortionType.NUMBER_SWAP.value,
    DistortionType.KRW_UNIT_ERROR.value,
    DistortionType.DATE_SHIFT.value,
    DistortionType.INCLUSIVITY_FLIP.value,
    DistortionType.CONDITION_FLIP.value,
    DistortionType.RANGE_WEAKEN.value,
    DistortionType.NEGATION_DROP.value,
}


def _bench_for(name: str):
    source, easy = _HANDLED_PAIRS[name]
    cases = generate_distortions(source, easy, ref_date=REF)
    return cases, run_distortion_bench(cases, verify, ref_date=REF)


def test_each_handled_distortion_is_caught_by_real_gate():
    for name in _HANDLED_PAIRS:
        cases, res = _bench_for(name)
        realized = {c.distortion_type.value for c in cases if not c.is_clean}
        # The pair's own distortion type must be realized by the generator.
        assert name in realized, f"{name} pattern not realized for pair {name!r}"
        # The REAL gate must catch it (recall 1.0) — load-bearing on M1/M2.
        assert res.per_type_recall.get(name) == 1.0, (
            f"real gate missed {name}: recall={res.per_type_recall}")


def test_real_gate_never_flags_faithful_clean_controls():
    # clean_fp_rate == 0.0 on every isolated corpus: faithful copies must PASS.
    # Before M2 this FAILED for the eligibility pairs (faithful 이상/미만 were
    # false-positive REVISE), making the gate unusable.
    for name in _HANDLED_PAIRS:
        _cases, res = _bench_for(name)
        assert res.clean_fp_rate == 0.0, f"{name}: faithful control flagged (fp)"


def test_real_gate_recall_high_across_all_handled_types():
    # Aggregate over every isolated corpus: for the distortion types this gate
    # is responsible for, realized-and-caught recall is 1.0, and no clean FP.
    handled_recalls: list[float] = []
    for name in _HANDLED_PAIRS:
        cases, res = _bench_for(name)
        assert res.clean_fp_rate == 0.0
        for dtype, recall in res.per_type_recall.items():
            if dtype in _GATE_HANDLED:
                handled_recalls.append(recall)
    assert handled_recalls, "no handled distortions were realized"
    assert min(handled_recalls) == 1.0, f"a handled distortion was missed: {handled_recalls}"
