import pytest

from ttobak.ir import BlockType
from ttobak.parse.pdf_parser import ParseError
from ttobak.parse.text_parser import parse_text

NOTICE = """# 청년 월세 한시 특별지원 안내

신청 기간은 2026년 7월 1일부터 2026년 8월 31일까지입니다.
지원 금액은 월 최대 200,000원입니다.

## 신청 자격
- 만 19세 이상 만 34세 이하 청년
- 부모와 따로 거주하는 무주택자
1. 주민센터 방문 신청
2. 온라인 신청
"""


def test_heading_detected_with_level():
    doc = parse_text(NOTICE, "text/markdown")
    headings = [b for b in doc.blocks if b.type == BlockType.HEADING]
    assert headings[0].text == "청년 월세 한시 특별지원 안내"
    assert headings[0].level == 1
    assert headings[1].text == "신청 자격"
    assert headings[1].level == 2


def test_paragraph_groups_consecutive_lines():
    doc = parse_text(NOTICE, "text/markdown")
    paragraphs = [b for b in doc.blocks if b.type == BlockType.PARAGRAPH]
    assert paragraphs[0].text == (
        "신청 기간은 2026년 7월 1일부터 2026년 8월 31일까지입니다.\n"
        "지원 금액은 월 최대 200,000원입니다."
    )


def test_bullet_and_numbered_lines_become_list_items():
    doc = parse_text(NOTICE, "text/markdown")
    items = [b.text for b in doc.blocks if b.type == BlockType.LIST_ITEM]
    assert items == [
        "- 만 19세 이상 만 34세 이하 청년",
        "- 부모와 따로 거주하는 무주택자",
        "1. 주민센터 방문 신청",
        "2. 온라인 신청",
    ]


def test_all_blocks_have_full_confidence():
    doc = parse_text(NOTICE, "text/markdown")
    assert all(b.confidence == 1.0 for b in doc.blocks)


def test_blank_lines_do_not_produce_blocks():
    doc = parse_text("첫 줄\n\n\n둘째 줄", "text/plain")
    texts = [b.text for b in doc.blocks]
    assert texts == ["첫 줄", "둘째 줄"]


def test_empty_input_raises_parse_error():
    """빈 입력이 blocks=[] Document로 통과하면 다운스트림 fidelity가 슬롯 0개로
    지어낸 쉬운본을 PASS시킬 수 있다 (pdf/hwp 파서와 동일하게 ParseError로 통일)."""
    with pytest.raises(ParseError):
        parse_text("", "text/plain")


def test_whitespace_only_input_raises_parse_error():
    with pytest.raises(ParseError):
        parse_text("   \n\t\n  ", "text/plain")


def test_bom_is_stripped_and_heading_still_detected():
    text = "﻿# 제목\n본문"
    doc = parse_text(text, "text/markdown")
    headings = [b for b in doc.blocks if b.type == BlockType.HEADING]
    assert headings[0].text == "제목"
    assert "﻿" not in doc.text()


def test_bom_only_input_raises_parse_error():
    with pytest.raises(ParseError):
        parse_text("﻿", "text/plain")
