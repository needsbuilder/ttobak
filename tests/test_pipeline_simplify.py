from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict
from ttobak.providers.fake import FakeProvider
from ttobak.result import EasyReadResult
from ttobak.pipeline import simplify


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)],
                    source_mime="text/plain", meta={"ref_date": "2026-07-01"})


def test_simplify_passes_without_revision():
    src = "건강보험료 본인부담금은 50,000원입니다. 2026년 8월 1일까지 내세요."
    provider = FakeProvider(["건강보험료는 50,000원입니다.\n2026년 8월 1일까지 내세요."])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=3)
    assert isinstance(result, EasyReadResult)
    assert result.verdict == Verdict.PASS
    assert result.revisions == 0
    assert result.level == Level.EASY
    assert "50,000원" in result.easy_text
    assert result.ker is not None
    assert result.fidelity.verdict == Verdict.PASS
    assert isinstance(result.pictograms, list)


def test_simplify_revises_rounded_amount_then_passes():
    src = "건강보험료 본인부담금은 1,295,400원입니다. 2026년 7월 17일까지 납부하셔야 합니다."
    provider = FakeProvider([
        "건강보험료는 약 130만 원입니다.\n2026년 7월 17일까지 내세요.",
        "건강보험료는 1,295,400원입니다.\n2026년 7월 17일까지 내세요.",
    ])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=3)
    assert result.revisions == 1
    assert result.verdict == Verdict.PASS
    assert result.fidelity.verdict == Verdict.PASS
    assert "1,295,400원" in result.easy_text
    assert "약 130만" not in result.easy_text


def test_simplify_negation_flip_routes_to_human_review_without_revising():
    src = "이 지원금은 외국인은 신청할 수 없습니다. 내국인만 신청 가능합니다."
    provider = FakeProvider(["이 지원금은 외국인도 신청할 수 있습니다.\n내국인도 신청할 수 있습니다."])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=3)
    assert result.fidelity.verdict == Verdict.HUMAN_REVIEW
    assert result.verdict == Verdict.HUMAN_REVIEW
    assert result.revisions == 0


def test_simplify_residual_failure_escalates_to_human_review():
    src = "본인부담금은 1,295,400원이며 2026년 7월 17일까지 납부하세요."
    provider = FakeProvider([
        "본인부담금은 약 130만 원입니다. 2026년 7월 17일까지 내세요.",
        "본인부담금은 약 130만 원입니다. 2026년 7월 17일까지 내세요.",
        "본인부담금은 약 130만 원입니다. 2026년 7월 17일까지 내세요.",
    ])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=2)
    assert result.revisions == 2
    assert result.fidelity.verdict == Verdict.REVISE
    assert result.verdict == Verdict.HUMAN_REVIEW
