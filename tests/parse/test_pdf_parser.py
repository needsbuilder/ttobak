import io

import pytest
from pypdf import PdfWriter

from ttobak.ir import BlockType, Document
from ttobak.parse._fixtures import make_minimal_pdf
from ttobak.parse.pdf_parser import (
    ParseError, parse_pdf, PDF_PRIMARY_CONFIDENCE, PDF_FALLBACK_CONFIDENCE,
)


def test_parse_pdf_extracts_text_with_full_confidence(pdf_bytes):
    doc = parse_pdf(pdf_bytes)
    assert isinstance(doc, Document)
    assert doc.source_mime == "application/pdf"
    assert "Ttobak PDF body" in doc.text()
    assert "Second visible line" in doc.text()
    assert all(b.type is BlockType.PARAGRAPH for b in doc.blocks)
    assert all(b.confidence == PDF_PRIMARY_CONFIDENCE for b in doc.blocks)
    assert doc.meta["parser"] == "pypdf"


def test_parse_pdf_one_block_per_nonblank_line(pdf_bytes):
    doc = parse_pdf(pdf_bytes)
    texts = [b.text for b in doc.blocks]
    assert "Ttobak PDF body" in texts
    assert "Second visible line" in texts
    assert "" not in texts


def test_parse_pdf_blank_page_raises_parse_error():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    with pytest.raises(ParseError, match="no extractable text"):
        parse_pdf(buf.getvalue())


def test_parse_pdf_garbage_bytes_raises_parse_error():
    with pytest.raises(ParseError):
        parse_pdf(b"this is definitely not a pdf")


def test_parse_pdf_falls_back_to_pdfminer(monkeypatch, pdf_bytes):
    import ttobak.parse.pdf_parser as mod

    class _EmptyPage:
        def extract_text(self):
            return ""

    class _EmptyReader:
        def __init__(self, *a, **k):
            self.pages = [_EmptyPage()]

    monkeypatch.setattr(mod, "PdfReader", _EmptyReader, raising=False)

    doc = parse_pdf(pdf_bytes)
    assert "Ttobak PDF body" in doc.text()
    assert doc.meta["parser"] == "pdfminer.six"
    assert all(b.confidence == PDF_FALLBACK_CONFIDENCE for b in doc.blocks)
