from __future__ import annotations

from ttobak.pictogram.lexicon import LEXICON
from ttobak.pictogram.models import PictogramRef

__all__ = ["match", "PictogramRef"]


def match(easy_text: str) -> list[PictogramRef]:
    """Look up pictogram refs for core concepts present in easy_text.

    Hand-dictionary substring lookup (spec 4.2.E: deliberately NOT general
    semantic matching). Deduplicates synonyms that share a glyph, preserving
    first-seen order in the text.
    """
    seen_glyphs: set[str] = set()
    refs: list[PictogramRef] = []
    matched: list[tuple[int, PictogramRef]] = []
    for keyword, ref in LEXICON.items():
        idx = easy_text.find(keyword)
        if idx != -1:
            matched.append((idx, ref))
    for _, ref in sorted(matched, key=lambda pair: pair[0]):
        if ref.glyph_id in seen_glyphs:
            continue
        seen_glyphs.add(ref.glyph_id)
        refs.append(ref)
    return refs
