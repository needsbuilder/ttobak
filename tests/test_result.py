from ttobak.result import EasyReadResult
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict, Severity
from ttobak.metric.models import KERReport, Violation
from ttobak.fidelity.models import FidelityReport, Slot, SlotType


def _doc() -> Document:
    return Document(
        blocks=[Block(type=BlockType.PARAGRAPH, text="건강보험료 1,295,400원을 2026년 7월 17일까지 내세요.")],
        source_mime="text/plain",
    )


def _ker() -> KERReport:
    return KERReport(
        score=81.0,
        level_estimate=2,
        sub_scores={"rule": 81.0},
        violations=[
            Violation(rule="sentence_length", span="한 문장", severity=Severity.MED, suggestion="문장을 나누세요.")
        ],
    )


def _fidelity() -> FidelityReport:
    return FidelityReport(
        slots=[Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY)],
        verdict=Verdict.PASS,
    )


def test_easy_read_result_holds_all_parts():
    result = EasyReadResult(
        source=_doc(),
        easy_text="건강보험료를 내세요.\n1,295,400원입니다.\n2026년 7월 17일까지 내세요.",
        level=Level.EASY,
        ker=_ker(),
        fidelity=_fidelity(),
        revisions=2,
        verdict=Verdict.PASS,
    )
    assert result.level is Level.EASY
    assert result.verdict is Verdict.PASS
    assert result.revisions == 2
    assert result.ker.score == 81.0
    assert result.fidelity.verdict is Verdict.PASS
    assert result.source.source_mime == "text/plain"


def test_easy_read_result_defaults_pictograms_and_revisions():
    result = EasyReadResult(
        source=_doc(),
        easy_text="쉬운 글.",
        level=Level.PLAIN,
        ker=_ker(),
        fidelity=_fidelity(),
        verdict=Verdict.HUMAN_REVIEW,
    )
    assert result.pictograms == []
    assert result.revisions == 0
    assert result.verdict is Verdict.HUMAN_REVIEW
