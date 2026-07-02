"""Public parse entry point: dispatch raw input to a format-specific parser."""
from __future__ import annotations

from pathlib import Path

from ttobak.ir import Document
from ttobak.parse.text_parser import UnsupportedMimeError, parse_text
from ttobak.parse.pdf_parser import parse_pdf, ParseError, PDF_MIME
from ttobak.parse.hwp_parser import parse_hwpx, UnsupportedFormatError, HWPX_MIME, HWP_MIME

__all__ = [
    "parse", "parse_pdf", "parse_hwpx",
    "ParseError", "UnsupportedFormatError", "UnsupportedMimeError",
    "PDF_MIME", "HWPX_MIME", "HWP_MIME",
]

_TEXT_MIMES = frozenset({"text/plain", "text/markdown"})


def _decode_bytes(data: bytes) -> str:
    """Decode raw text bytes, falling back utf-8 -> cp949 (bug fix).

    Korean public/admin documents are frequently saved as cp949/EUC-KR. A
    utf-8-only decode leaked a raw UnicodeDecodeError for such input; both
    encodings failing now raises the documented ParseError instead.
    """
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        pass
    try:
        return data.decode("cp949")
    except UnicodeDecodeError as exc:
        raise ParseError(f"could not decode text bytes as utf-8 or cp949: {exc}") from exc


def _to_text(source: bytes | str | Path) -> str:
    if isinstance(source, Path):
        return _decode_bytes(source.read_bytes())
    if isinstance(source, bytes):
        return _decode_bytes(source)
    return source


def _as_bytes(source: bytes | str | Path, mime: str) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    raise ParseError(f"{mime} requires bytes or a Path, got a str source")


def parse(source: bytes | str | Path, mime: str) -> Document:
    """Parse ``source`` of the given ``mime`` into a Document IR.

    Text (text/plain, text/markdown) via the text parser; PDF via pypdf/pdfminer;
    HWPX best-effort. Legacy .hwp -> UnsupportedFormatError; any other unknown
    mime -> UnsupportedMimeError (no silent degradation).
    """
    if mime in _TEXT_MIMES:
        return parse_text(_to_text(source), mime)
    if mime == PDF_MIME:
        return parse_pdf(_as_bytes(source, mime), source_mime=mime)
    if mime == HWPX_MIME:
        return parse_hwpx(_as_bytes(source, mime), source_mime=mime)
    if mime == HWP_MIME:
        raise UnsupportedFormatError("legacy .hwp binary is out of MVP scope; convert to HWPX or PDF")
    raise UnsupportedMimeError(f"unsupported mime type: {mime!r}")
