"""Exact-match verification of HIGH-criticality slots (spec 6.4, 6.8).

NUMERIC/DATE/MONEY/CONTACT/SCOPE slots must survive verbatim (by normalized
value) in the easy text. Rounding is a distortion UNLESS all three conditions
of spec 6.8 hold simultaneously: (1) the source span contains a hedge token,
(2) the easy text preserves the same hedge token, (3) the slot's normalized
value is in the document-level rounding allowlist (empty by default, opt-in).
"""
from __future__ import annotations

import re
from datetime import date

from ttobak.common import Severity
from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.normalize import normalize_date, normalize_money, normalize_phone

ROUNDING_HEDGE_TOKENS: tuple[str, ...] = ("약", "대략", "여", "내외", "쯤", "가량")

_MONEY_SPAN = re.compile(r"(?:[\d,]+|[일이삼사오육칠팔구십백천만억조\s]+)\s*원")
_DATE_SPAN = re.compile(
    r"\d{4}\s*[년.\-/]\s*\d{1,2}\s*[월.\-/]\s*\d{1,2}\s*일?(?:\s*(?:전\s*)?까지)?"
    r"|D\s*-\s*\d+|\d+\s*일\s*(?:후|뒤|이내)"
)
_CONTACT_SPAN = re.compile(r"\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}")


def _easy_money_values(easy_text: str) -> set[str]:
    values: set[str] = set()
    for m in _MONEY_SPAN.finditer(easy_text):
        try:
            values.add(str(normalize_money(m.group(0))))
        except ValueError:
            continue
    return values


def _easy_date_values(easy_text: str, ref_date: date) -> set[str]:
    values: set[str] = set()
    for m in _DATE_SPAN.finditer(easy_text):
        try:
            iso, _incl = normalize_date(m.group(0), ref_date)
        except ValueError:
            continue
        values.add(iso)
    return values


def _easy_contact_values(easy_text: str) -> set[str]:
    values: set[str] = set()
    for m in _CONTACT_SPAN.finditer(easy_text):
        try:
            values.add(normalize_phone(m.group(0)))
        except ValueError:
            continue
    return values


def _rounding_exception_ok(slot: Slot, easy_text: str, rounding_allowlist: set[str]) -> bool:
    """Spec 6.8: rounding PASSes only if all three conditions hold."""
    src_has_hedge = any(h in slot.raw_span for h in ROUNDING_HEDGE_TOKENS)
    easy_has_hedge = any(h in easy_text for h in ROUNDING_HEDGE_TOKENS)
    opted_in = slot.normalized_value in rounding_allowlist
    return src_has_hedge and easy_has_hedge and opted_in


def verify_high_slots(slots: list[Slot], easy_text: str, ref_date: date,
                      rounding_allowlist: set[str] | None = None) -> list[Slot]:
    """Return the HIGH slots that FAIL to survive verbatim in ``easy_text``."""
    allowlist = rounding_allowlist or set()
    money_values = _easy_money_values(easy_text)
    date_values = _easy_date_values(easy_text, ref_date)
    contact_values = _easy_contact_values(easy_text)

    failed: list[Slot] = []
    for slot in slots:
        if slot.criticality != Severity.HIGH:
            continue
        survived = False
        if slot.type == SlotType.MONEY:
            survived = slot.normalized_value in money_values
        elif slot.type == SlotType.DATE:
            iso = slot.normalized_value.split("|", 1)[0]
            survived = iso in date_values
        elif slot.type == SlotType.CONTACT:
            survived = slot.normalized_value in contact_values
        elif slot.type in (SlotType.NUMERIC, SlotType.SCOPE):
            survived = slot.normalized_value in money_values or slot.normalized_value in easy_text
        else:
            survived = slot.normalized_value in easy_text

        if not survived and slot.type == SlotType.MONEY:
            if _rounding_exception_ok(slot, easy_text, allowlist):
                survived = True

        if not survived:
            failed.append(slot)
    return failed
