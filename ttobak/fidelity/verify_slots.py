"""Exact-match verification of HIGH-criticality slots (spec 6.4, 6.8).

NUMERIC/DATE/MONEY/CONTACT/SCOPE/AGENCY slots must survive (by normalized
value; AGENCY by surface substring) in the easy text. NUMERIC accepts
표기 변형(콤마·퍼센트/%·고유어 수사 1~10)을 같은 값으로 인정한다.
한계(문서화): 쉬운본이 원문에 없는 기관명을 창작하는 방향의 환각은 원문
슬롯 기반 생존 검증으로는 잡지 못한다 — NER 교차검증 로드맵.

Rounding is a distortion UNLESS all three conditions
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
    count_values,
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


def _ambiguous_month_days(slots: list[Slot]) -> set[tuple[int, int]]:
    """같은 월-일이 서로 다른 연도로 2회 이상 등장하는 DATE 슬롯의 (월, 일) 집합.

    이 경우 연도가 생략된 쉬운본 날짜는 어느 마감을 가리키는지 알 수 없으므로
    특정 슬롯의 생존 근거로 쓰면 안 된다 (무연도 표현이 target 연도로 디폴트되어
    복수 마감일 전부에 매칭 -> 누락이 PASS 되는 게이트 구멍).
    """
    years: dict[tuple[int, int], set[int]] = {}
    for slot in slots:
        if slot.type != SlotType.DATE:
            continue
        iso, _incl = _split_date_value(slot.normalized_value)
        y, mo, d = (int(p) for p in iso.split("-"))
        years.setdefault((mo, d), set()).add(y)
    return {md for md, ys in years.items() if len(ys) >= 2}


def _easy_date_inclusivity(easy_text: str, iso: str, ref_date: date,
                           ambiguous_month_days: set[tuple[int, int]] = frozenset(),
                           ) -> bool | None:
    """Return the inclusivity the easy text assigns to the date ``iso``.

    Scans every month/day span (year optional) in ``easy_text``; for the one
    whose resolved date equals ``iso`` it reports inclusivity from its trailing
    qualifier (까지 -> True, 전/이전 -> False, no qualifier -> False). Returns
    ``None`` when no span resolves to ``iso`` (the date itself is absent).

    연도 생략 표현은 원문에 같은 월-일·다른 연도 마감이 공존하면(``ambiguous_month_days``)
    매칭에서 배제한다 — 그렇지 않으면 연도가 다른 모든 슬롯에 동시 매칭된다.
    """
    target_y, target_mo, target_d = (int(p) for p in iso.split("-"))
    for m in _DATE_FLEX.finditer(easy_text):
        y_raw, mo_raw, d_raw, qualifier = m.groups()
        mo, d = int(mo_raw), int(d_raw)
        if y_raw is None and (mo, d) in ambiguous_month_days:
            continue  # 무연도 표현은 어느 연도를 뜻하는지 판별 불가
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


def _operand_occurrences(easy_text: str, operand: str) -> list[int]:
    """쉬운본 안 오퍼랜드 등장 위치들 (경계 인식).

    앞에 숫자/콤마가 붙은 매칭은 배제한다 — '5,000명'이 '15,000명'의 꼬리로
    매칭돼 다른 임계값이 생존 처리되는 것을 막는다.
    """
    if not operand:
        return []
    pat = re.compile(r"(?<![\d,])" + re.escape(operand))
    return [m.start() for m in pat.finditer(easy_text)]


def _easy_boundary_ops(easy_text: str, operand: str) -> list[str]:
    """쉬운본에서 ``operand`` 각 등장 직후의 경계 연산자 심볼 목록 (등장 순).

    연산자 키워드가 없으면 ''(삭제됨)로 기록한다. 오퍼랜드 자체가 없으면 빈 목록.
    (기존 구현은 첫 등장만 검사해, 같은 오퍼랜드가 서로 다른 연산자로 여러 번
    나오는 문서에서 무손상 쉬운본이 오탐되고 뒤쪽 슬롯의 반전을 놓쳤다.)
    """
    ops: list[str] = []
    for start in _operand_occurrences(easy_text, operand):
        window = easy_text[start + len(operand): start + len(operand) + 8]
        for kw in _OPERATOR_KEYWORDS:
            if kw in window:
                ops.append(BOUNDARY_OPERATORS[kw])
                break
        else:
            ops.append("")
    return ops


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
    numeric_values = count_values(easy_text)
    ambiguous_md = _ambiguous_month_days(slots)

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
                easy_text, iso, ref_date, ambiguous_md) is not None
        elif slot.type == SlotType.CONTACT:
            survived = slot.normalized_value in contact_values
        elif slot.type == SlotType.SCOPE:
            # The operand (number+unit) must survive; operator identity is
            # checked in detect_drift_flips. A SCOPE slot whose operand is
            # present is "recovered" here so it never routes to REVISE — its
            # operator integrity is a HUMAN_REVIEW concern, not a verbatim miss.
            # (경계 인식 매칭 — 다른 수의 부분문자열로 생존 처리되면 안 된다.)
            operand = _operand_surface(slot.raw_span)
            survived = bool(_operand_occurrences(easy_text, operand))
        elif slot.type == SlotType.NUMERIC:
            # 정규값 집합 비교 — 표기 변형(3,000명/3000명, 32퍼센트/32%,
            # 1명/한 명)은 생존, 값이 다르면 부분문자열이어도 실패.
            survived = slot.normalized_value in numeric_values
        elif slot.type == SlotType.AGENCY:
            # 공백 무시 비교 — Easy-Read의 복합어 띄어쓰기('강서 구청')는
            # 왜곡이 아니다. 바꿔치기('송파 구청')는 여전히 실패한다.
            survived = (slot.normalized_value.replace(" ", "")
                        in easy_text.replace(" ", ""))
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
    ambiguous_md = _ambiguous_month_days(slots)
    for slot in slots:
        if slot.criticality != Severity.HIGH:
            continue

        if slot.type == SlotType.DATE:
            iso, src_inclusive = _split_date_value(slot.normalized_value)
            if not src_inclusive:
                continue  # only an inclusive source deadline can be weakened
            easy_inclusive = _easy_date_inclusivity(easy_text, iso, ref_date, ambiguous_md)
            if easy_inclusive is None:
                continue  # date absent -> a recoverable miss, not a flip
            if easy_inclusive != src_inclusive:
                flips.append(
                    f"날짜 포함 경계('까지')가 쉬운본에서 약화/반전됨: {iso}"
                )

    # SCOPE: 같은 오퍼랜드가 여러 임계값으로 재사용될 수 있으므로 슬롯별
    # '첫 등장' 비교가 아니라, 오퍼랜드별로 쉬운본의 연산자 목록과 다중집합
    # 대응을 본다 — 소스 슬롯(오프셋 순)마다 같은 연산자 등장을 하나씩 소비하고,
    # 소비할 수 없으면 반전/삭제로 판정한다. (한계: 오퍼랜드가 같고 연산자
    # 다중집합까지 동일한 쌍맞교환 재배치는 탐지 불가 — 문서화된 한계.)
    scope_slots = sorted(
        (s for s in slots
         if s.criticality == Severity.HIGH and s.type == SlotType.SCOPE
         and s.normalized_value in (">=", ">", "<=", "<")),
        key=lambda s: s.source_offset,
    )
    by_operand: dict[str, list[Slot]] = {}
    for slot in scope_slots:
        operand = _operand_surface(slot.raw_span)
        if operand:
            by_operand.setdefault(operand, []).append(slot)

    for operand, group in by_operand.items():
        available = _easy_boundary_ops(easy_text, operand)
        if not available:
            continue  # operand absent -> recoverable miss, not a flip
        for slot in group:
            if slot.normalized_value in available:
                available.remove(slot.normalized_value)
                continue
            got = available[0] if available else ""
            detail = "삭제됨" if got == "" else f"'{got}'로 변경됨"
            flips.append(
                f"자격 경계 연산자('{slot.normalized_value}', {slot.raw_span})가 쉬운본에서 {detail}"
            )

    return flips
