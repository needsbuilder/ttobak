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

# 보존된 부정 마커 직후 이 신호가 붙으면 이중부정(재부정) — 마커가 표면상
# 살아 있어도 의미는 반전됐을 수 있으므로 HUMAN_REVIEW로 회부한다 (fail-safe:
# 오탐은 사람 검수로 흡수, 미탐은 왜곡 통과이므로 보수적으로 잡는다).
_REVERSAL_CUES = ("지 않", "지않", "지는 않", "그렇지 않", "라고 생각", "아니")
_REVERSAL_WINDOW = 18

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

    A flip is reported when (a) the source contains a negation marker that is
    absent from the easy text, or (b) a preserved marker is immediately
    re-negated in the easy text (이중부정 — 예: '제외되지 않고', '제외됩니다
    라고 생각하기 쉽지만 그렇지 않으며'). 마커 '존재'만 보면 (b)류 의미 반전이
    PASS로 새므로, 보존된 마커 주변의 반전 신호를 함께 본다.
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

    # (b) 이중부정: 소스에 있던 마커 패턴이 쉬운본에도 있으나, 등장 직후
    # 짧은 창 안에 재부정 신호가 붙는 경우.
    for pat in _COMPILED:
        src_m = pat.search(source_text)
        if not src_m:
            continue
        for m in pat.finditer(easy_text):
            window = easy_text[m.end(): m.end() + _REVERSAL_WINDOW]
            if any(cue in window for cue in _REVERSAL_CUES):
                marker = m.group(0).replace(" ", "")
                flips.append(
                    f"부정 표현 '{marker}'이(가) 쉬운본에서 재부정(이중부정)되어 "
                    f"의미가 반전될 수 있음"
                )
                break
    return flips
