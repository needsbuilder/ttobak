from __future__ import annotations

from ttobak.pictogram.lexicon import FALSE_POSITIVE_COMPOUNDS, LEXICON
from ttobak.pictogram.models import PictogramRef

__all__ = ["match", "PictogramRef"]


def _is_false_positive_occurrence(text: str, keyword: str, idx: int) -> bool:
    """True if the keyword occurrence at idx is part of a guarded compound word.

    Checks the 2-syllable windows immediately left and right of the occurrence
    against the keyword's stoplist (bug fix; see lexicon.FALSE_POSITIVE_COMPOUNDS).
    """
    stoplist = FALSE_POSITIVE_COMPOUNDS.get(keyword)
    if not stoplist:
        return False
    left_bigram = text[max(idx - 1, 0):idx + 1]
    right_bigram = text[idx:idx + 2]
    return left_bigram in stoplist or right_bigram in stoplist


def _find_first_valid_occurrence(text: str, keyword: str) -> int:
    """Find the first occurrence of keyword that isn't a guarded false positive."""
    start = 0
    while True:
        idx = text.find(keyword, start)
        if idx == -1:
            return -1
        if not _is_false_positive_occurrence(text, keyword, idx):
            return idx
        start = idx + 1


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
        idx = _find_first_valid_occurrence(easy_text, keyword)
        if idx != -1:
            matched.append((idx, ref))
    for _, ref in sorted(matched, key=lambda pair: pair[0]):
        if ref.glyph_id in seen_glyphs:
            continue
        seen_glyphs.add(ref.glyph_id)
        refs.append(ref)
    return refs
