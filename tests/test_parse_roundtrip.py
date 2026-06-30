from pathlib import Path

from ttobak.ir import BlockType
from ttobak.parse import parse

FIXTURE = Path(__file__).parent / "fixtures" / "notice_health_insurance.txt"


def test_plain_text_roundtrip_is_exact():
    # No markdown markup, no blank lines -> each line is one paragraph block,
    # so .text() must reproduce the input verbatim.
    src = "보험료를 납부해 주세요.\n납부 기한은 2026년 7월 25일입니다.\n문의 1577-1000"
    doc = parse(src, "text/plain")
    assert doc.text() == src


def test_fixture_block_types_snapshot():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    snapshot = [(b.type.value, b.level) for b in doc.blocks]
    assert snapshot == [
        ("heading", 1),
        ("paragraph", 0),
        ("heading", 2),
        ("list_item", 0),
        ("list_item", 0),
        ("list_item", 0),
        ("paragraph", 0),
    ]


def test_fixture_preserves_critical_facts_in_block_text():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    joined = doc.text()
    # Fidelity-critical spans must survive parsing verbatim (spec §3.1).
    assert "1,295,400원" in joined
    assert "2026년 7월 25일" in joined
    assert "1577-1000" in joined


def test_fixture_all_confidence_full():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    assert all(b.confidence == 1.0 for b in doc.blocks)


def test_fixture_first_heading_text():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    headings = [b for b in doc.blocks if b.type == BlockType.HEADING]
    assert headings[0].text == "2026년 7월분 건강보험료 납부 안내"
