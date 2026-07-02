"""Plain-text and markdown-ish parser into the Ttobak IR.

Text is the PRIMARY, trusted input tier (spec §7.1): extraction confidence is
always 1.0 because no lossy extraction occurs. Detects markdown ATX headings,
bullet/numbered list items, and groups remaining lines into paragraphs.
"""
from __future__ import annotations

import re

from ttobak.ir import Block, BlockType, Document
from ttobak.parse.pdf_parser import ParseError

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^\s*([-*•]|\d+[.)])\s+\S")


class UnsupportedMimeError(ValueError):
    """Raised when parse() is given a MIME type it cannot handle.

    Per spec §7.3 the engine degrades gracefully with an explicit error rather
    than silently producing garbage.
    """


def parse_text(text: str, mime: str) -> Document:
    """Parse plain/markdown text into structured IR blocks.

    - ``#``..``######`` lines -> HEADING (level = number of hashes).
    - ``-``/``*``/``•``/``1.``/``1)`` lines -> LIST_ITEM (original line, stripped).
    - Consecutive remaining non-blank lines -> one PARAGRAPH (joined by newlines).
    - Blank lines separate paragraphs and are not emitted as blocks.

    All blocks carry confidence 1.0 (trusted text tier).

    Raises ParseError on empty/whitespace-only input, matching pdf_parser and
    hwp_parser (bug fix: a silent blocks=[] Document let downstream fidelity
    checks vacuously PASS a fabricated easy-read with zero slots).
    """
    text = text.lstrip("﻿")  # strip leading UTF-8 BOM (bug fix)
    if not text.strip():
        raise ParseError("text input is empty or contains no extractable content")

    blocks: list[Block] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            blocks.append(
                Block(
                    type=BlockType.PARAGRAPH,
                    text="\n".join(paragraph_lines),
                    confidence=1.0,
                )
            )
            paragraph_lines.clear()

    for raw_line in text.split("\n"):
        line = raw_line.rstrip()
        if not line.strip():
            flush_paragraph()
            continue

        heading = _HEADING_RE.match(line)
        if heading is not None:
            flush_paragraph()
            blocks.append(
                Block(
                    type=BlockType.HEADING,
                    text=heading.group(2).strip(),
                    level=len(heading.group(1)),
                    confidence=1.0,
                )
            )
            continue

        if _LIST_RE.match(line):
            flush_paragraph()
            blocks.append(
                Block(
                    type=BlockType.LIST_ITEM,
                    text=line.strip(),
                    confidence=1.0,
                )
            )
            continue

        paragraph_lines.append(line.strip())

    flush_paragraph()
    return Document(blocks=blocks, source_mime=mime)
