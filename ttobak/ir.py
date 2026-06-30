"""Intermediate Representation (IR) for Ttobak.

This is the canonical, shared data model that every downstream module
(parse, pipeline, metric, fidelity, render) imports. Do NOT redefine these
names elsewhere — import them from here.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CAPTION = "caption"


class Block(BaseModel):
    type: BlockType
    text: str = ""
    level: int = 0
    cells: list[list[str]] | None = None
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = 1.0


class Document(BaseModel):
    blocks: list[Block]
    source_mime: str
    meta: dict = Field(default_factory=dict)

    def text(self) -> str:
        """Join every block's text with newlines (round-trippable plain text)."""
        return "\n".join(block.text for block in self.blocks)
