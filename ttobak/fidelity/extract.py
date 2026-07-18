"""Slot extraction from source IR (spec 6.3).

Regex + normalizers form the deterministic core so the test suite stays
deterministic and offline. Extraction over-collects (recall first); the
verifier decides survival.

구현 범위 (정직한 경계): MONEY/DATE/CONTACT/SCOPE/NEGATION은 정규화 기반
정확 검증, AGENCY(기관명 접미사 사전)/NUMERIC(단위명사 개수)은 best-effort
패턴 추출이다. PERSON/DURATION/ELIGIBILITY/CONDITIONAL/MODALITY 추출과
NER 기반 기관명 보강은 로드맵 (spec 6.3의 전체 슬롯 타입은 models.SlotType).
"""
from __future__ import annotations

import re
from datetime import date

from ttobak.common import Severity
from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.normalize import (
    BOUNDARY_OPERATORS,
    COUNT_RE,
    detect_boundary,
    normalize_count,
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
# 오퍼랜드가 콤마 그룹 숫자(30,000원)일 때 절단되지 않도록 숫자 대안을 먼저 둔다.
# ([^\s,]* 단독이면 '30,000원 미만' -> '000원 미만'으로 잘려 게이트가 뚫린다.)
_SCOPE_OPERAND = r"(?:\d{1,3}(?:,\d{3})+|\d+)[^\s,]*|[^\s,]*"
_SCOPE_RE = re.compile(
    r"(?:" + _SCOPE_OPERAND + r")\s*(?:" + "|".join(BOUNDARY_OPERATORS) + r")"
)
_NEGATION_RE = re.compile(r"[^\s,.]*(?:제외|불가|금지|아니|없|지\s*않)[^\s,.]*")
# 기관명 (best-effort): 행정기관 접미사 사전 + 자주 쓰는 단독 기관명.
# '공사'(construction 동음이의)·단독 '청'('신청'류 오인)은 의도적으로 제외.
# 접미사 사전에 없는 기관·조사 결합 변형은 문서화된 한계 (NER 보강 로드맵).
_AGENCY_SUFFIXES = (
    "구청|시청|군청|도청|주민센터|행정복지센터|복지센터|복지관|보건소|공단"
    "|세무서|우체국|경찰서|소방서|교육청|지원센터|위원회|재단|협회"
)
_AGENCY_NAMED = (
    "국세청|병무청|경찰청|검찰청|기상청|조달청|통계청|관세청|산림청|특허청"
    "|소방청|질병관리청|건강보험심사평가원"
)
_AGENCY_RE = re.compile(rf"[가-힣]+(?:{_AGENCY_SUFFIXES})|(?:{_AGENCY_NAMED})")


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

    for m in _AGENCY_RE.finditer(text):
        _add(slots, m.group(0), m.group(0), SlotType.AGENCY, m.start())

    for m in COUNT_RE.finditer(text):
        _add(slots, m.group(0), normalize_count(m.group(1), m.group(2)),
             SlotType.NUMERIC, m.start())

    return slots
