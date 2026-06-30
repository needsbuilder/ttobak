"""Plain-text and markdown-ish parser into the Ttobak IR.

Text is the PRIMARY, trusted input tier (spec §7.1): extraction confidence is
always 1.0 because no lossy extraction occurs.
"""
from __future__ import annotations

from ttobak.ir import Block, BlockType, Document


class UnsupportedMimeError(ValueError):
    """Raised when parse() is given a MIME type it cannot handle.

    Per spec §7.3 the engine degrades gracefully with an explicit error rather
    than silently producing garbage.
    """


def parse_text(text: str, mime: str) -> Document:
    """Parse plain text into a single-paragraph Document (placeholder body).

    Replaced with full heading/list detection in Task 9. Kept minimal
    here so the dispatcher task is independently testable.
    """
    block = Block(type=BlockType.PARAGRAPH, text=text, confidence=1.0)
    return Document(blocks=[block], source_mime=mime)
