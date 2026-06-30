"""Pictogram reference contract (Task 31 owns the real implementation).

This is a STUB contract used during Phase-1 skeleton (Task 16–20). Task 31 will provide
the real PictogramRef with full icon library integration. Do NOT overwrite Task 31's version.
"""
from __future__ import annotations

from pydantic import BaseModel, field_validator


class PictogramRef(BaseModel):
    """Reference to a pictogram / icon for Easy-Read presentation."""

    concept: str
    set: str
    glyph_id: str
    caption: str

    @field_validator("glyph_id")
    @classmethod
    def _reject_data_uri(cls, v: str) -> str:
        """Reject data: URIs — spec §9.4 forbids inlined/base64-embedded glyphs.

        Only relative paths (e.g. 'mulberry/money.svg') and HTTPS URLs are
        accepted; data: URIs of any case are rejected with ValueError.
        """
        if v.lower().startswith("data:"):
            raise ValueError(
                "glyph_id must be a relative file path or https URL, "
                f"not a data: URI (got {v!r}). "
                "Spec §9.4 forbids inlined/base64-embedded glyphs."
            )
        return v
