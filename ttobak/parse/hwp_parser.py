"""HWPX -> Document via hwp-hwpx-parser (best-effort, M8).

Legacy .hwp (OLE binary) is out of MVP scope (spec 7.1/12.3/15.4) and rejected
with UnsupportedFormatError. HWPX is BEST-EFFORT: clean parses yield blocks at
sub-1.0 confidence; unreadable/empty input degrades to an explicit ParseError
(never a silent empty Document, spec 3.1/7.3).
"""
from __future__ import annotations

import os
import tempfile

from ttobak.ir import Block, BlockType, Document
from ttobak.parse.pdf_parser import ParseError

HWPX_MIME = "application/vnd.hancom.hwpx"
HWP_MIME = "application/x-hwp"
HWPX_CONFIDENCE = 0.7


class UnsupportedFormatError(ValueError):
    """Raised for inputs outside MVP parser scope (e.g. legacy .hwp)."""


def _text_to_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        blocks.append(Block(type=BlockType.PARAGRAPH, text=line, confidence=HWPX_CONFIDENCE))
    return blocks


def parse_hwpx(data: bytes, *, source_mime: str = HWPX_MIME) -> Document:
    """Parse HWPX ``data`` (best-effort) into a Document.

    Writes bytes to a temp file because hwp-hwpx-parser reads from a path.
    """
    if source_mime == HWP_MIME:
        raise UnsupportedFormatError("legacy .hwp binary is out of MVP scope; convert to HWPX or PDF")

    try:
        from hwp_hwpx_parser import Reader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ParseError(f"hwp-hwpx-parser is not installed: {exc}") from exc

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            with Reader(tmp_path) as reader:
                if not getattr(reader, "is_valid", True):
                    raise ParseError("hwp-hwpx-parser reported invalid HWPX")
                text = reader.text or ""
        except ParseError:
            raise
        except Exception as exc:
            raise ParseError(f"hwp-hwpx-parser failed: {exc}") from exc
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    blocks = _text_to_blocks(text)
    if not blocks:
        raise ParseError("HWPX contained no extractable text")
    return Document(blocks=blocks, source_mime=source_mime, meta={"parser": "hwp-hwpx-parser", "best_effort": True})
