"""Slot extraction from source IR (spec 6.3).

Redundant extraction: regex + normalizers form the deterministic core; spaCy
``ko_core_news_lg`` NER is OPTIONAL and gated behind import availability so the
test suite stays deterministic and offline. Extraction over-collects (recall
first); the verifier decides survival.
"""
from __future__ import annotations

import re
from datetime import date

from ttobak.common import Severity
from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.normalize import (
    BOUNDARY_OPERATORS,
    detect_boundary,
    normalize_date,
    normalize_money,
    normalize_phone,
)
from ttobak.ir import Document

_MONEY_RE = re.compile(r"(?:약\s*)?(?:[\d,]+|[일이삼사오육칠팔구십백천만억조\s]+)\s*원")
_DATE_RE = re.compile(
    r"\d{4}\s*[년.\-/]\s*\d{1,2}\s*[월.\-/]\s*\d{1,2}\s*일?(?:\s*(?:전\s*)?까지)?"
    r"|D\s*-\s*\d+|\d+\s*일\s*(?:후|뒤|이내)"
)
_CONTACT_RE = re.compile(r"(?:\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4})")
_SCOPE_RE = re.compile(r"[^\s,]*\s*(?:" + "|".join(BOUNDARY_OPERATORS) + r")")
_NEGATION_RE = re.compile(r"[^\s,.]*(?:제외|불가|금지|아니|없|지\s*않)[^\s,.]*")


def _add(slots, span, value, stype, offset, polarity=True, crit=Severity.HIGH):
    slots.append(Slot(raw_span=span.strip(), normalized_value=value, type=stype,
                      polarity=polarity, source_offset=offset, criticality=crit))


def extract_slots(doc: Document, ref_date: date) -> list[Slot]:
    """Extract typed preservation-required fact slots from the source document."""
    text = doc.text()
    slots: list[Slot] = []

    for m in _MONEY_RE.finditer(text):
        try:
            value = normalize_money(m.group(0))
        except ValueError:
            continue
        _add(slots, m.group(0), str(value), SlotType.MONEY, m.start())

    for m in _DATE_RE.finditer(text):
        try:
            iso, inclusive = normalize_date(m.group(0), ref_date)
        except ValueError:
            continue
        value = f"{iso}|inclusive" if inclusive else iso
        _add(slots, m.group(0), value, SlotType.DATE, m.start())

    for m in _CONTACT_RE.finditer(text):
        try:
            value = normalize_phone(m.group(0))
        except ValueError:
            continue
        _add(slots, m.group(0), value, SlotType.CONTACT, m.start())

    for m in _SCOPE_RE.finditer(text):
        symbol = detect_boundary(m.group(0))
        if symbol in (">=", ">", "<=", "<"):
            _add(slots, m.group(0), symbol, SlotType.SCOPE, m.start())

    for m in _NEGATION_RE.finditer(text):
        _add(slots, m.group(0), m.group(0).strip(), SlotType.NEGATION, m.start(), polarity=False)

    return slots
