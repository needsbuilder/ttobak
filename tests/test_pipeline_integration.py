"""Integration smoke test for the pipeline with real metric/fidelity modules."""
from ttobak.pipeline import simplify
from ttobak.providers.fake import FakeProvider
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict
from ttobak.result import EasyReadResult


def test_simplify_end_to_end_with_real_metric_and_fidelity():
    doc = Document(
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="건강보험료 1,295,400원을 2026년 7월 17일까지 납부하여야 합니다."),
        ],
        source_mime="text/plain",
        meta={"ref_date": "2026-06-30"},
    )
    provider = FakeProvider(["건강보험료를 내세요.\n1,295,400원입니다.\n2026년 7월 17일까지 내세요."])
    result = simplify(doc, Level.EASY, provider, max_revise=3)

    assert isinstance(result, EasyReadResult)
    assert result.source is doc
    assert result.level is Level.EASY
    assert result.verdict in (Verdict.PASS, Verdict.REVISE, Verdict.HUMAN_REVIEW)
    assert result.revisions >= 0
    assert isinstance(result.ker.score, float)
    assert isinstance(result.fidelity.verdict, Verdict)
    assert len(provider.calls) >= 1
