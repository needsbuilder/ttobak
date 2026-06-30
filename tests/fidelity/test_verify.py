from datetime import date

from ttobak.common import Verdict
from ttobak.ir import Block, BlockType, Document
from ttobak.fidelity import verify

REF = date(2026, 7, 10)


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)], source_mime="text/plain")


def test_clean_control_passes():
    src = _doc("보험료 1,295,400원을 2026년 7월 17일까지 납부하세요.")
    easy = "이번 달 보험료는 1,295,400원입니다. 2026년 7월 17일까지 내세요."
    report = verify(src, easy, REF)
    assert report.verdict == Verdict.PASS
    assert report.exact_fail_count == 0
    assert report.failed_slots == []


def test_number_swap_caught_and_revises():
    report = verify(_doc("보험료는 30,000원입니다."), "보험료는 3,000원입니다.", REF)
    assert report.verdict == Verdict.REVISE
    assert report.exact_fail_count == 1
    assert any(s.normalized_value == "30000" for s in report.failed_slots)


def test_date_drift_caught_and_revises():
    report = verify(_doc("신청 기한은 2026년 7월 17일까지입니다."), "신청은 2026년 7월 7일까지 하세요.", REF)
    assert report.verdict == Verdict.REVISE
    assert report.exact_fail_count == 1


def test_negation_flip_human_review():
    report = verify(_doc("외국인은 지원 대상에서 제외됩니다."), "외국인도 지원 대상에 포함됩니다.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW
    assert report.drift_flags


def test_report_lists_all_extracted_slots():
    src = _doc("보험료 30,000원을 2026년 7월 17일까지 내세요.")
    report = verify(src, "보험료 30,000원을 2026년 7월 17일까지 내세요.", REF)
    types = {s.type.value for s in report.slots}
    assert "money" in types
    assert "date" in types
    assert report.verdict == Verdict.PASS
