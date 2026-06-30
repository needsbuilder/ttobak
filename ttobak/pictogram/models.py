"""Pictogram reference contract (Task 31 owns the real implementation).

This is a STUB contract used during Phase-1 skeleton (Task 16–20). Task 31 will provide
the real PictogramRef with full icon library integration. Do NOT overwrite Task 31's version.
"""
from __future__ import annotations

from pydantic import BaseModel


class PictogramRef(BaseModel):
    """Reference to a pictogram / icon for Easy-Read presentation."""

    concept: str
    set: str
    glyph_id: str
    caption: str
