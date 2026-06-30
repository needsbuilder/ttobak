"""Tokenizer + sentence splitter for K-ER rules.

All kiwipiepy access is isolated here so rule functions can be tested with
injected Token lists (deterministic, no live tokenizer). kiwipiepy is LGPL-3.0
and used as a separate, unmodified dependency (spec 9.1/9.4).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_SENT_SPLIT = re.compile(r"(?<=[.!?。])\s+|\n+")


@dataclass
class Token:
    form: str
    tag: str


_kiwi = None


def _get_kiwi():
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi  # lazy import; LGPL separate dep
        _kiwi = Kiwi()
    return _kiwi


def tokenize(text: str) -> list[Token]:
    """Morphologically tokenize ``text`` into (form, POS-tag) Tokens."""
    kiwi = _get_kiwi()
    out: list[Token] = []
    for tok in kiwi.tokenize(text):
        out.append(Token(form=tok.form, tag=str(tok.tag)))
    return out


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on terminal punctuation / newlines."""
    parts = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    return parts
