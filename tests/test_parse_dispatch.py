import pytest

from ttobak.ir import BlockType, Document
from ttobak.parse import parse, ParseError
from ttobak.parse.text_parser import UnsupportedMimeError


def test_parse_returns_document_for_plain_text():
    doc = parse("국민건강보험공단 안내문입니다.", "text/plain")
    assert isinstance(doc, Document)
    assert doc.source_mime == "text/plain"
    assert doc.text() == "국민건강보험공단 안내문입니다."


def test_parse_accepts_bytes_input():
    raw = "보험료 납부 안내".encode("utf-8")
    doc = parse(raw, "text/plain")
    assert doc.text() == "보험료 납부 안내"


def test_parse_accepts_path_input(tmp_path):
    p = tmp_path / "notice.txt"
    p.write_text("청년 주거지원 안내", encoding="utf-8")
    doc = parse(p, "text/plain")
    assert doc.text() == "청년 주거지원 안내"
    assert doc.source_mime == "text/plain"


def test_parse_routes_markdown_mime_to_text_parser():
    doc = parse("# 제목", "text/markdown")
    assert isinstance(doc, Document)
    assert doc.source_mime == "text/markdown"


def test_parse_raises_on_unsupported_mime():
    with pytest.raises(UnsupportedMimeError) as exc:
        parse(b"whatever", "application/zip")
    assert "application/zip" in str(exc.value)


def test_parse_first_block_is_paragraph_for_single_line():
    doc = parse("한 줄짜리 안내입니다.", "text/plain")
    assert doc.blocks[0].type == BlockType.PARAGRAPH
    assert doc.blocks[0].confidence == 1.0


def test_parse_decodes_cp949_bytes():
    raw = "설날 인사말 안내".encode("cp949")
    doc = parse(raw, "text/plain")
    assert doc.text() == "설날 인사말 안내"


def test_parse_raises_parse_error_for_undecodable_bytes():
    bad = b"\xff\xfe\x00\x01"
    with pytest.raises(ParseError):
        parse(bad, "text/plain")


def test_parse_strips_utf8_bom_from_bytes():
    raw = "# 제목\n본문".encode("utf-8-sig")
    doc = parse(raw, "text/markdown")
    headings = [b for b in doc.blocks if b.type == BlockType.HEADING]
    assert headings[0].text == "제목"
    assert "﻿" not in doc.text()
