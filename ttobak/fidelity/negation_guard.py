"""NegationGuard: dedicated single-token negation flip detector (spec 6.7).

NLI/embeddings frequently miss single-token negation flips, so a dedicated
rule scans explicit polarity markers (제외/아니/불가/없/금지/말/~지 않) and pairs
each source negation with the easy text. A dropped or reversed negation is a
hard failure routed to HUMAN_REVIEW (never auto-revised).
"""
from __future__ import annotations

import re

NEGATION_PATTERNS: list[str] = [
    r"제외",
    r"아니",
    r"불가",
    r"없",
    r"금지",
    r"말아야",
    r"마십시오",
    r"지\s*않",
    r"못\s*하",
]

_AFFIRMATION_TOKENS = ("포함", "가능", "있습니다", "할 수 있", "허용")

_COMPILED = [re.compile(p) for p in NEGATION_PATTERNS]


def scan_negations(text: str) -> list[str]:
    """Return the surface negation markers present in ``text`` (deduped, in order)."""
    found: list[str] = []
    for pat in _COMPILED:
        m = pat.search(text)
        if m:
            marker = m.group(0).replace(" ", "")
            if marker not in found:
                found.append(marker)
    return found


def check_negation_flip(source_text: str, easy_text: str) -> list[str]:
    """Detect source negations dropped or reversed in the easy text.

    A flip is reported when the source contains a negation marker that is
    absent from the easy text AND the easy text contains an affirmation token.
    Returns a list of human-readable flip descriptions; empty means no flip.
    """
    src_negs = scan_negations(source_text)
    if not src_negs:
        return []
    easy_negs = scan_negations(easy_text)
    has_affirmation = any(tok in easy_text for tok in _AFFIRMATION_TOKENS)
    flips: list[str] = []
    for marker in src_negs:
        if marker not in easy_negs:
            flips.append(
                f"부정 표현 '{marker}'이(가) 쉬운본에서 누락/반전됨"
                + (" (긍정 단언 감지)" if has_affirmation else "")
            )
    return flips
