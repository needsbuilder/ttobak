"""Public parse entry point: dispatch raw input to a format-specific parser.

    parse(source: bytes | str | Path, mime: str) -> Document
"""
from __future__ import annotations

from pathlib import Path

from ttobak.ir import Document
from ttobak.parse.text_parser import UnsupportedMimeError, parse_text

_TEXT_MIMES = frozenset({"text/plain", "text/markdown"})


def _to_text(source: bytes | str | Path) -> str:
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if isinstance(source, bytes):
        return source.decode("utf-8")
    return source


def parse(source: bytes | str | Path, mime: str) -> Document:
    """Parse ``source`` of the given ``mime`` into a structured Document.

    Supported now: ``text/plain``, ``text/markdown``. Unsupported MIME types
    raise :class:`UnsupportedMimeError` (graceful, explicit degradation).
    """
    if mime in _TEXT_MIMES:
        return parse_text(_to_text(source), mime)
    raise UnsupportedMimeError(f"unsupported mime type: {mime!r}")
