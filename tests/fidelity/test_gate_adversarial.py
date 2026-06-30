"""Adversarial reproducers for the Fidelity gate (final-review M1/M2).

These exercise the REAL ``verify()`` over a REAL ``Document`` with adversarial
easy-text rewrites that are demo-able false-negatives in the headline safety
gate. Each "flip" must NOT pass (route to HUMAN_REVIEW, since the meaning change
is unsafe and not auto-recoverable); each faithful CONTROL must PASS.

M1 = date inclusivity (까지 vs 전에/이전에) flip.
M2 = eligibility boundary operators (이상/초과/이하/미만).
"""
from datetime import date

from ttobak.common import Verdict
from ttobak.fidelity import verify
from ttobak.fidelity.models import SlotType
from ttobak.ir import Block, BlockType, Document

REF = date(2026, 7, 1)


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)], source_mime="text/plain")


# ---------------------------------------------------------------------------
# M1 — date inclusivity (까지 vs 전에/이전에) flip is unsafe -> HUMAN_REVIEW
# ---------------------------------------------------------------------------

_M1_SOURCE = "건강보험료를 2026년 7월 17일까지 납부하세요."


def test_m1_kkaji_to_jeone_is_human_review():
    # "까지" (inclusive of the 17th) -> "전에" (before the 17th): deadline meaning flip.
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일 전에 내세요.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m1_kkaji_to_ijeone_is_human_review():
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일 이전에 내세요.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m1_kkaji_dropped_bare_date_not_pass():
    # "까지" dropped entirely (bare date): inclusivity boundary lost -> must not PASS.
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일 내세요.", REF)
    assert report.verdict != Verdict.PASS


def test_m1_faithful_kkaji_control_passes_for_date():
    report = verify(_doc(_M1_SOURCE), "건강보험료를 2026년 7월 17일까지 내세요.", REF)
    assert report.verdict == Verdict.PASS
    # the date slot itself must not be among the failures
    assert not any(s.type == SlotType.DATE for s in report.failed_slots)


# ---------------------------------------------------------------------------
# M2 — eligibility boundary operators
#   faithful copies must PASS; operator flips must -> HUMAN_REVIEW
# ---------------------------------------------------------------------------

def test_m2_faithful_isang_passes():
    src = "만 65세 이상만 신청 가능합니다."
    report = verify(_doc(src), src, REF)
    assert report.verdict == Verdict.PASS
    assert not any(s.type == SlotType.SCOPE for s in report.failed_slots)


def test_m2_faithful_miman_passes():
    src = "소득 100만원 미만 가구가 대상입니다."
    report = verify(_doc(src), src, REF)
    assert report.verdict == Verdict.PASS
    assert not any(s.type == SlotType.SCOPE for s in report.failed_slots)


def test_m2_faithful_chogwa_passes():
    src = "정원 100명 초과 시 마감합니다."
    report = verify(_doc(src), src, REF)
    assert report.verdict == Verdict.PASS
    assert not any(s.type == SlotType.SCOPE for s in report.failed_slots)


def test_m2_isang_to_iha_flip_is_human_review():
    src = "만 65세 이상만 신청 가능합니다."
    easy = "만 65세 이하만 신청할 수 있어요."
    report = verify(_doc(src), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m2_miman_to_iha_flip_is_human_review():
    src = "소득 100만원 미만 가구가 대상입니다."
    easy = "소득 100만원 이하 가구가 대상이에요."
    report = verify(_doc(src), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW


def test_m2_boundary_dropped_in_easy_is_caught():
    # Boundary keyword dropped entirely from easy text: meaning lost while the
    # operand "65세" is preserved -> unsafe flip -> HUMAN_REVIEW.
    src = "만 65세 이상만 신청 가능합니다."
    easy = "만 65세 신청 가능합니다."
    report = verify(_doc(src), easy, REF)
    assert report.verdict == Verdict.HUMAN_REVIEW
    assert report.drift_flags


# ---------------------------------------------------------------------------
# Regression — the money-shot must still work
# ---------------------------------------------------------------------------

def test_money_shot_rounding_revises():
    src = _doc("보험료 1,295,400원을 납부하세요.")
    report = verify(src, "이번 달 보험료는 약 130만 원입니다.", REF)
    assert report.verdict == Verdict.REVISE
    assert any(s.normalized_value == "1295400" for s in report.failed_slots)


def test_money_shot_exact_passes():
    src = _doc("보험료 1,295,400원을 납부하세요.")
    report = verify(src, "이번 달 보험료는 1,295,400원입니다.", REF)
    assert report.verdict == Verdict.PASS
