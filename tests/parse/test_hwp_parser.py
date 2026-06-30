import pytest

from ttobak.ir import BlockType, Document
from ttobak.parse._fixtures import make_minimal_hwpx
from ttobak.parse.pdf_parser import ParseError
from ttobak.parse.hwp_parser import parse_hwpx, UnsupportedFormatError, HWPX_CONFIDENCE


def test_parse_hwpx_extracts_paragraphs_best_effort(hwpx_bytes):
    doc = parse_hwpx(hwpx_bytes)
    assert isinstance(doc, Document)
    assert doc.source_mime == "application/vnd.hancom.hwpx"
    assert "청년 주거지원 안내문" in doc.text()
    assert "신청 기간은 정해져 있습니다." in doc.text()
    assert all(b.type is BlockType.PARAGRAPH for b in doc.blocks)
    assert all(b.confidence == HWPX_CONFIDENCE for b in doc.blocks)
    assert doc.meta["parser"] == "hwp-hwpx-parser"
    assert doc.meta["best_effort"] is True


def test_parse_hwpx_rejects_legacy_hwp_mime(hwpx_bytes):
    with pytest.raises(UnsupportedFormatError, match="legacy .hwp"):
        parse_hwpx(hwpx_bytes, source_mime="application/x-hwp")


def test_parse_hwpx_corrupt_input_raises_parse_error():
    with pytest.raises(ParseError):
        parse_hwpx(b"PK\x03\x04 not a real hwpx zip body")


def test_parse_hwpx_empty_document_raises_parse_error():
    empty = make_minimal_hwpx([])  # valid OWPML, zero paragraphs
    with pytest.raises(ParseError, match="no extractable text"):
        parse_hwpx(empty)
