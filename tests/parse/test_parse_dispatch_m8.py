from pathlib import Path

import pytest

from ttobak.ir import Document
from ttobak.parse import (
    parse, ParseError, UnsupportedFormatError, UnsupportedMimeError,
    PDF_MIME, HWPX_MIME, HWP_MIME,
)
from ttobak.parse._fixtures import make_minimal_pdf, make_minimal_hwpx


def test_parse_dispatches_pdf_bytes():
    doc = parse(make_minimal_pdf(["Dispatch via mime"]), PDF_MIME)
    assert isinstance(doc, Document)
    assert "Dispatch via mime" in doc.text()
    assert doc.meta["parser"] in {"pypdf", "pdfminer.six"}


def test_parse_dispatches_hwpx_bytes():
    doc = parse(make_minimal_hwpx(["고지서 본문 한 줄"]), HWPX_MIME)
    assert "고지서 본문 한 줄" in doc.text()
    assert doc.meta["best_effort"] is True


def test_parse_reads_pdf_from_path(tmp_path: Path):
    p = tmp_path / "doc.pdf"
    p.write_bytes(make_minimal_pdf(["From a file path"]))
    assert "From a file path" in parse(p, PDF_MIME).text()


def test_parse_rejects_legacy_hwp_mime():
    with pytest.raises(UnsupportedFormatError):
        parse(make_minimal_hwpx(["x"]), HWP_MIME)


def test_parse_unknown_mime_raises_unsupported():
    with pytest.raises(UnsupportedMimeError):
        parse(b"whatever", "application/zip")


def test_parse_str_source_for_pdf_is_rejected():
    with pytest.raises(ParseError, match="bytes"):
        parse("not bytes", PDF_MIME)
