"""PDF -> Document. pypdf primary, pdfminer.six fallback (M8)."""
from __future__ import annotations

import io

from pdfminer.high_level import extract_text as _pdfminer_extract_text
from pypdf import PdfReader

from ttobak.ir import Block, BlockType, Document

PDF_MIME = "application/pdf"
PDF_PRIMARY_CONFIDENCE = 1.0
PDF_FALLBACK_CONFIDENCE = 0.6


class ParseError(ValueError):
    """Raised when input cannot be parsed into any usable text."""


def _lines_to_blocks(text: str, confidence: float) -> list[Block]:
    blocks: list[Block] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        blocks.append(Block(type=BlockType.PARAGRAPH, text=line, confidence=confidence))
    return blocks


def _pypdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages)


def _pdfminer_text(data: bytes) -> str:
    return _pdfminer_extract_text(io.BytesIO(data)) or ""


def parse_pdf(data: bytes, *, source_mime: str = PDF_MIME) -> Document:
    """Parse PDF ``data`` to a Document.

    pypdf primary (confidence 1.0). If pypdf yields no usable text, fall back to
    pdfminer.six and tag blocks with reduced confidence (0.6). If both yield
    nothing, raise ParseError (no silent empty Document).
    """
    primary_error: Exception | None = None
    try:
        text = _pypdf_text(data)
    except Exception as exc:
        primary_error = exc
        text = ""

    blocks = _lines_to_blocks(text, PDF_PRIMARY_CONFIDENCE)
    if blocks:
        return Document(blocks=blocks, source_mime=source_mime, meta={"parser": "pypdf"})

    try:
        fb_text = _pdfminer_text(data)
    except Exception as exc:
        raise ParseError(
            f"both pypdf and pdfminer.six failed to read PDF: pypdf={primary_error!r} pdfminer={exc!r}"
        ) from exc

    fb_blocks = _lines_to_blocks(fb_text, PDF_FALLBACK_CONFIDENCE)
    if not fb_blocks:
        raise ParseError("PDF contained no extractable text")
    return Document(blocks=fb_blocks, source_mime=source_mime, meta={"parser": "pdfminer.six"})
