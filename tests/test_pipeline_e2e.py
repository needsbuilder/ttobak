from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict
from ttobak.providers.fake import FakeProvider
from ttobak.result import EasyReadResult
from ttobak.pipeline import simplify


def _gojiseo_doc() -> Document:
    return Document(
        blocks=[
            Block(type=BlockType.HEADING, text="2026년 7월분 건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="귀하의 2026년 7월분 건강보험료 본인부담금은 1,295,400원입니다."),
            Block(type=BlockType.PARAGRAPH, text="납부기한은 2026년 7월 17일까지입니다."),
            Block(type=BlockType.PARAGRAPH, text="문의: 국민건강보험공단 1577-1000."),
        ],
        source_mime="text/plain",
        meta={"ref_date": "2026-07-01"},
    )


def test_end_to_end_gojiseo_money_shot():
    doc = _gojiseo_doc()
    provider = FakeProvider([
        ("2026년 7월에 낼 건강보험료를 알려드립니다.\n내야 할 돈은 약 130만 원입니다.\n"
         "2026년 7월 17일까지 내세요.\n궁금하면 국민건강보험공단 1577-1000으로 전화하세요."),
        ("2026년 7월에 낼 건강보험료를 알려드립니다.\n내야 할 돈은 1,295,400원입니다.\n"
         "2026년 7월 17일까지 내세요.\n궁금하면 국민건강보험공단 1577-1000으로 전화하세요."),
    ])
    result = simplify(doc, Level.EASY, provider, max_revise=3)

    assert isinstance(result, EasyReadResult)
    assert result.level == Level.EASY
    assert result.source is doc
    assert result.revisions == 1
    assert result.verdict == Verdict.PASS
    assert result.fidelity.verdict == Verdict.PASS
    assert result.fidelity.exact_fail_count == 0
    assert "1,295,400원" in result.easy_text
    assert "2026년 7월 17일" in result.easy_text
    assert "1577-1000" in result.easy_text
    assert "약 130만" not in result.easy_text
    assert isinstance(result.ker.score, float)
    assert 0.0 <= result.ker.score <= 100.0
    assert isinstance(result.pictograms, list)  # 전화/돈 may match; attribute must be a list
