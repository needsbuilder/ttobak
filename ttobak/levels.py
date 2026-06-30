"""Output reading levels (canonical contract).

PLAIN = 보통 읽기 (Plain Language, 문해수준 3, text-centric).
EASY  = 쉬운 글 (Easy Korean, 문해수준 1–2, layout/whitespace/pictogram-centric).
"""

from enum import Enum


class Level(str, Enum):
    PLAIN = "plain"
    EASY = "easy"
