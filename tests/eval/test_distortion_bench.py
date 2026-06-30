"""Bench ARITHMETIC unit tests (NOT a real-gate recall test).

These exercise ``run_distortion_bench``'s scoring math (per-type recall,
clean-FP rate, residual rate, P/R/F1, confusion) using a STUB ``verify_fn``
that flags by hardcoded literal markers. They deliberately do NOT call the real
``ttobak.fidelity.verify`` — a recall of 1.0 here proves the bench arithmetic is
correct, NOT that the gate actually catches anything. The gate's real recall is
covered by ``test_distortion_bench_real_gate.py``.
"""
from datetime import date

from ttobak.common import Verdict
from ttobak.eval.distortion_bench import BenchResult, DistortionCase, DistortionType, run_distortion_bench
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Document


def _case(case_id, dtype, distorted, *, clean, expected_pass):
    return DistortionCase(
        case_id=case_id, source_text="원문 30,000원 강서구청 7월 17일까지",
        easy_text="쉬운 글 30,000원 강서구청 7월 17일까지", distorted_text=distorted,
        distortion_type=dtype, is_clean=clean, expected_pass=expected_pass)


def make_verify_fn(catch_markers, false_alarm_texts):
    """STUB gate: flags by literal markers. Exercises bench MATH, not the gate."""
    def verify_fn(source: Document, easy_text: str, ref_date: date) -> FidelityReport:
        caught = any(m in easy_text for m in catch_markers)
        false_alarm = easy_text in false_alarm_texts
        verdict = Verdict.HUMAN_REVIEW if (caught or false_alarm) else Verdict.PASS
        return FidelityReport(slots=[], verdict=verdict)
    return verify_fn


def test_bench_arithmetic_result_shape():
    cases = [
        _case("c-clean", DistortionType.CLEAN, "쉬운 글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "쉬운 글 3,000원", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원"], set()), ref_date=date(2026, 7, 1))
    assert isinstance(res, BenchResult)
    assert res.n_cases == 2 and res.n_clean == 1


def test_bench_arithmetic_per_type_recall_and_pass_residual():
    cases = [
        _case("c-clean", DistortionType.CLEAN, "clean글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "num 3,000원", clean=False, expected_pass=False),
        _case("c-date", DistortionType.DATE_SHIFT, "date 7월 7일", clean=False, expected_pass=False),
        _case("c-neg", DistortionType.NEGATION_DROP, "neg 포함됩니다", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원", "7월 7일"], set()), ref_date=date(2026, 7, 1))
    assert res.per_type_recall["number_swap"] == 1.0
    assert res.per_type_recall["date_shift"] == 1.0
    assert res.per_type_recall["negation_drop"] == 0.0
    assert round(res.overall_recall, 4) == round(2 / 3, 4)
    assert res.clean_fp_rate == 0.0
    assert round(res.pass_residual_distortion_rate, 4) == round(1 / 3, 4)


def test_bench_arithmetic_clean_fp_rate_counts_false_alarms():
    cases = [
        _case("c-clean1", DistortionType.CLEAN, "alarm글", clean=True, expected_pass=True),
        _case("c-clean2", DistortionType.CLEAN, "ok글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "num 3,000원", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원"], {"alarm글"}), ref_date=date(2026, 7, 1))
    assert res.n_clean == 2 and res.clean_fp_rate == 0.5
    assert res.confusion["clean_flagged_fp"] == 1
    assert res.confusion["distortion_caught_tp"] == 1


def test_bench_arithmetic_perfect_stub_has_zero_residual_and_full_recall():
    cases = [
        _case("c-clean", DistortionType.CLEAN, "clean글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "num 3,000원", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원"], set()), ref_date=date(2026, 7, 1))
    assert res.overall_recall == 1.0 and res.clean_fp_rate == 0.0
    assert res.pass_residual_distortion_rate == 0.0 and res.overall_f1 == 1.0
