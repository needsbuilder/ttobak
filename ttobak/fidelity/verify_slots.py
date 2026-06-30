"""Exact-match verification of HIGH-criticality slots (spec 6.4, 6.8).

NUMERIC/DATE/MONEY/CONTACT/SCOPE slots must survive verbatim (by normalized
value) in the easy text. Rounding is a distortion UNLESS all three conditions
of spec 6.8 hold simultaneously: (1) the source span contains a hedge token,
(2) the easy text preserves the same hedge token, (3) the slot's normalized
value is in the document-level rounding allowlist (empty by default, opt-in).

Two classes of HIGH-slot failure exist:
  * *recoverable exact-match misses* (a number/date/money was dropped or
    changed) -> returned by :func:`verify_high_slots`, routed to REVISE.
  * *unsafe semantic drifts* (a date INCLUSIVITY flip 까지<->전/이전, or an
    eligibility BOUNDARY-operator flip 이상<->이하/미만<->이하) -> returned by
    :func:`detect_drift_flips`, routed to HUMAN_REVIEW. These preserve the raw
    number yet invert the meaning, so they must never auto-revise.
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

ROUNDING_HEDGE_TOKENS: tuple[str, ...] = ("약", "대략", "여", "내외", "쯤", "가량")

_MONEY_SPAN = re.compile(r"(?:[\d,]+|[일이삼사오육칠팔구십백천만억조\s]+)\s*원")
_DATE_SPAN = re.compile(
    r"\d{4}\s*[년.\-/]\s*\d{1,2}\s*[월.\-/]\s*\d{1,2}\s*일?(?:\s*(?:전\s*)?까지)?"
    r"|D\s*-\s*\d+|\d+\s*일\s*(?:후|뒤|이내)"
)
_CONTACT_SPAN = re.compile(r"\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}")

# Flexible month/day matcher (year optional) with a trailing inclusivity
# qualifier (까지 / 전 / 이전). Used to read the inclusivity the easy text
# assigns to a date that the source emitted with a known year.
_DATE_FLEX = re.compile(
    r"(?:(\d{4})\s*[년.\-/]\s*)?(\d{1,2})\s*[월.\-/]\s*(\d{1,2})\s*일?"
    r"(\s*(?:이?전|까지))?"
)

# Boundary keywords that act as comparison operators (까지/부터 are date/range
# markers handled by the DATE path, not eligibility boundaries).
_OPERATOR_KEYWORDS: tuple[str, ...] = ("이상", "초과", "이하", "미만")


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


def _split_date_value(normalized_value: str) -> tuple[str, bool]:
    """Split a DATE slot value 'ISO' or 'ISO|inclusive' into (iso, inclusive)."""
    if "|" in normalized_value:
        iso, flag = normalized_value.split("|", 1)
        return iso, flag == "inclusive"
    return normalized_value, False


def _easy_date_inclusivity(easy_text: str, iso: str, ref_date: date) -> bool | None:
    """Return the inclusivity the easy text assigns to the date ``iso``.

    Scans every month/day span (year optional) in ``easy_text``; for the one
    whose resolved date equals ``iso`` it reports inclusivity from its trailing
    qualifier (까지 -> True, 전/이전 -> False, no qualifier -> False). Returns
    ``None`` when no span resolves to ``iso`` (the date itself is absent).
    """
    target_y, target_mo, target_d = (int(p) for p in iso.split("-"))
    for m in _DATE_FLEX.finditer(easy_text):
        y_raw, mo_raw, d_raw, qualifier = m.groups()
        mo, d = int(mo_raw), int(d_raw)
        y = int(y_raw) if y_raw else target_y
        if (y, mo, d) != (target_y, target_mo, target_d):
            continue
        q = (qualifier or "").strip()
        if not q:
            return False  # bare date: inclusivity boundary dropped
        return ("까지" in q) and ("전" not in q)
    return None


def _operand_surface(raw_span: str) -> str:
    """Strip the trailing boundary keyword, leaving the operand (e.g. '65세')."""
    operand = raw_span
    for kw in _OPERATOR_KEYWORDS:
        if operand.endswith(kw):
            operand = operand[: -len(kw)]
            break
    return operand.strip()


def _easy_boundary_after(easy_text: str, operand: str) -> str | None:
    """Read the boundary operator keyword that follows ``operand`` in easy text.

    Returns the operator SYMBOL (>=, >, <=, <) when a boundary keyword appears
    within a short window after the operand, '' when the operand is present but
    carries NO boundary keyword (dropped), or ``None`` when the operand itself
    is absent.
    """
    idx = easy_text.find(operand)
    if idx == -1:
        return None
    window = easy_text[idx + len(operand): idx + len(operand) + 8]
    for kw in _OPERATOR_KEYWORDS:
        if kw in window:
            return BOUNDARY_OPERATORS[kw]
    return ""


def verify_high_slots(slots: list[Slot], easy_text: str, ref_date: date,
                      rounding_allowlist: set[str] | None = None) -> list[Slot]:
    """Return the HIGH slots that FAIL to survive verbatim in ``easy_text``.

    Only *recoverable* exact-match misses are returned (number/date/money/
    contact dropped or changed). Unsafe semantic drifts (inclusivity / boundary
    flips that preserve the raw value) are reported separately by
    :func:`detect_drift_flips`.
    """
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
            iso, _incl = _split_date_value(slot.normalized_value)
            survived = iso in date_values or iso in easy_text or _easy_date_inclusivity(
                easy_text, iso, ref_date) is not None
        elif slot.type == SlotType.CONTACT:
            survived = slot.normalized_value in contact_values
        elif slot.type == SlotType.SCOPE:
            # The operand (number+unit) must survive; operator identity is
            # checked in detect_drift_flips. A SCOPE slot whose operand is
            # present is "recovered" here so it never routes to REVISE — its
            # operator integrity is a HUMAN_REVIEW concern, not a verbatim miss.
            operand = _operand_surface(slot.raw_span)
            survived = bool(operand) and operand in easy_text
        elif slot.type == SlotType.NUMERIC:
            survived = slot.normalized_value in money_values or slot.normalized_value in easy_text
        else:
            survived = slot.normalized_value in easy_text

        if not survived and slot.type == SlotType.MONEY:
            if _rounding_exception_ok(slot, easy_text, allowlist):
                survived = True

        if not survived:
            failed.append(slot)
    return failed


def detect_drift_flips(slots: list[Slot], easy_text: str, ref_date: date) -> list[str]:
    """Detect unsafe meaning flips that preserve the raw value (spec 6.4/6.8).

    These route to HUMAN_REVIEW (never auto-revise):
      * DATE inclusivity flip — source '까지' (inclusive) vs easy '전/이전'
        (exclusive) or a bare date that dropped '까지'.
      * SCOPE boundary-operator flip — source 이상/초과/이하/미만 changed to a
        different operator, or the boundary keyword dropped entirely.
    """
    flips: list[str] = []
    for slot in slots:
        if slot.criticality != Severity.HIGH:
            continue

        if slot.type == SlotType.DATE:
            iso, src_inclusive = _split_date_value(slot.normalized_value)
            if not src_inclusive:
                continue  # only an inclusive source deadline can be weakened
            easy_inclusive = _easy_date_inclusivity(easy_text, iso, ref_date)
            if easy_inclusive is None:
                continue  # date absent -> a recoverable miss, not a flip
            if easy_inclusive != src_inclusive:
                flips.append(
                    f"날짜 포함 경계('까지')가 쉬운본에서 약화/반전됨: {iso}"
                )

        elif slot.type == SlotType.SCOPE:
            src_symbol = slot.normalized_value
            if src_symbol not in (">=", ">", "<=", "<"):
                continue
            operand = _operand_surface(slot.raw_span)
            if not operand:
                continue
            easy_symbol = _easy_boundary_after(easy_text, operand)
            if easy_symbol is None:
                continue  # operand absent -> recoverable miss, not a flip
            if easy_symbol != src_symbol:
                detail = "삭제됨" if easy_symbol == "" else f"'{easy_symbol}'로 변경됨"
                flips.append(
                    f"자격 경계 연산자('{src_symbol}', {slot.raw_span})가 쉬운본에서 {detail}"
                )

    return flips
