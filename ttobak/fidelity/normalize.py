"""Korean number / money / date / phone normalizers and boundary-operator table.

Spec sections 6.4, 6.6, 6.8, 14.1. Pure-Python deterministic core so the unit
suite can target recall 1.0 without external model/network dependencies.
``korean-number`` and ``dateparser`` are documented optional cross-checks; the
deterministic algorithms below are authoritative for tests.
"""
from __future__ import annotations

import re

_DIGITS = {
    "영": 0, "공": 0,
    "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
    "육": 6, "륙": 6, "칠": 7, "팔": 8, "구": 9,
}
_SMALL_UNITS = {"십": 10, "백": 100, "천": 1000}
_BIG_UNITS = {"만": 10**4, "억": 10**8, "조": 10**12, "경": 10**16}
_HEDGE_TOKENS = ("약", "대략", "여", "내외", "쯤", "가량")
# Order matters: strip longer affixes first so '원정' is caught before '원'.
# '금' is a prefix marker (e.g. '금 1,200,000원정'), stripped as an affix.
_MONEY_AFFIX = ("원정", "원", "금")


def _parse_korean_chunk(chunk: str) -> int:
    """Parse a sub-만 Korean numeral chunk (digits + 십/백/천) into an int.

    Handles mixed Arabic digits (e.g. '5천', '2천', '3만' sub-chunks).
    Arabic digits accumulate positionally before a unit multiplier.
    Korean digit characters overwrite `current` (no positional accumulation).
    """
    if chunk == "":
        return 0
    if chunk.isdigit():
        return int(chunk)
    total = 0
    current = 0
    arabic_buf = ""
    for ch in chunk:
        if ch.isdigit():
            arabic_buf += ch
        elif ch in _DIGITS:
            if arabic_buf:
                current = int(arabic_buf)
                arabic_buf = ""
            current = _DIGITS[ch]
        elif ch in _SMALL_UNITS:
            if arabic_buf:
                current = int(arabic_buf)
                arabic_buf = ""
            unit = _SMALL_UNITS[ch]
            total += (current if current else 1) * unit
            current = 0
        else:
            raise ValueError(f"unparsable Korean numeral char: {ch!r} in {chunk!r}")
    if arabic_buf:
        # trailing Arabic digits with no unit: treat as plain number
        total += int(arabic_buf)
    else:
        total += current
    return total


def normalize_korean_number(text: str) -> int:
    """Convert mixed Korean/Arabic numeral text into an int.

    Handles myriad units 만/억/조/경, sub-units 십/백/천, plain digits, commas,
    and a leading hedge token (약/대략/...). Examples: '삼만원'->30000,
    '약 3억 원'->300000000, '3만5천원'->35000.
    """
    s = text.strip()
    for hedge in _HEDGE_TOKENS:
        s = s.replace(hedge, "")
    for affix in _MONEY_AFFIX:
        s = s.replace(affix, "")
    s = s.replace(",", "").replace(" ", "")
    if s == "":
        raise ValueError(f"no numeral content in {text!r}")
    if s.isdigit():
        return int(s)

    total = 0
    buffer = ""
    found_big = False
    for ch in s:
        if ch in _BIG_UNITS:
            chunk_val = _parse_korean_chunk(buffer) if buffer else 1
            total += chunk_val * _BIG_UNITS[ch]
            buffer = ""
            found_big = True
        else:
            buffer += ch
    if buffer:
        total += _parse_korean_chunk(buffer)
    if total == 0 and not found_big:
        raise ValueError(f"unparsable numeral: {text!r}")
    return total


def normalize_money(text: str) -> int:
    """Normalize a Korean money expression to an integer KRW amount.

    Strips currency affixes (원/원정/금) and hedge tokens, then delegates to
    :func:`normalize_korean_number`. Examples: '1,295,400원'->1295400,
    '약 3억 원'->300000000.
    """
    return normalize_korean_number(text)


from datetime import date, timedelta

# Boundary-operator table (spec 6.4 / 14.1). Generator must not weaken these.
BOUNDARY_OPERATORS: dict[str, str] = {
    "이상": ">=",
    "초과": ">",
    "이하": "<=",
    "미만": "<",
    "까지": "inclusive",
    "부터": "from",
}

_DATE_YMD = re.compile(r"(\d{4})\s*[년.\-/]\s*(\d{1,2})\s*[월.\-/]\s*(\d{1,2})\s*일?")
_DATE_REL_DMINUS = re.compile(r"D\s*-\s*(\d+)")
_DATE_REL_AFTER = re.compile(r"(\d+)\s*일\s*(?:후|뒤|이내)")
_PHONE_KEEP = re.compile(r"\d")


def normalize_date(text: str, ref_date: date) -> tuple[str, bool]:
    """Normalize an absolute or relative Korean date to (ISO-8601, inclusive).

    ``inclusive`` is True only when the span carries '까지' WITHOUT a
    weakening '전'/'이전' qualifier. Relative forms 'D-N' and 'N일 후/뒤/이내'
    resolve against ``ref_date`` (spec failure-mode 4: RELATIVE_BASE = document date).
    """
    s = text.strip()
    has_kkaji = "까지" in s
    has_before = ("전" in s) or ("이전" in s)
    inclusive = has_kkaji and not has_before

    m = _DATE_YMD.search(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(y, mo, d).isoformat(), inclusive

    m = _DATE_REL_DMINUS.search(s)
    if m:
        return (ref_date + timedelta(days=int(m.group(1)))).isoformat(), inclusive

    m = _DATE_REL_AFTER.search(s)
    if m:
        return (ref_date + timedelta(days=int(m.group(1)))).isoformat(), inclusive

    raise ValueError(f"unparsable date: {text!r}")


def normalize_phone(text: str) -> str:
    """Reduce a phone/contact number to a digits-only canonical form."""
    digits = "".join(_PHONE_KEEP.findall(text))
    if not digits:
        raise ValueError(f"no phone digits in {text!r}")
    return digits


def detect_boundary(text: str) -> str | None:
    """Return the boundary-operator symbol present in ``text``, else None.

    Iterates the table so '이상'/'이하' keys match before bare substrings.
    """
    for keyword, symbol in BOUNDARY_OPERATORS.items():
        if keyword in text:
            return symbol
    return None


# --- Bare counts with unit nouns (spec 6.3 NUMERIC, best-effort) -------------
# 금액(원)·연월일·전화번호는 각자 MONEY/DATE/CONTACT 슬롯이 담당하므로 단위
# 목록에서 의도적으로 제외한다. '(?<![\d,])'는 '5,000명'이 '15,000명'의 꼬리로
# 매칭되는 부분문자열 오인을 막는다 (SCOPE 오퍼랜드 매칭과 동일 원칙).
# '개'는 '개월'(기간, DURATION 로드맵)의 접두로 오매칭되지 않게 (?!월) 가드.
COUNT_UNITS: tuple[str, ...] = (
    "명", "건", "회", "개", "가구", "세대", "곳", "세", "%", "퍼센트",
)
_COUNT_UNIT_ALT = "|".join("개(?!월)" if u == "개" else u for u in COUNT_UNITS)
COUNT_RE = re.compile(
    r"(?<![\d,])(\d{1,3}(?:,\d{3})+|\d+)\s*(" + _COUNT_UNIT_ALT + r")"
)
# 쉬운 글은 '1명'을 '한 명'으로 풀어 쓴다 — 고유어 수사(1~10)는 같은 값으로
# 인정한다. 쉬운본 매칭 전용(관대화 방향)이라 왜곡을 통과시키는 쪽으로는
# 작동하지 않는다.
# 문서화된 한계 (모두 과잉 표시 방향 — 왜곡이 아닌데 REVISE가 날 수 있음,
# 왜곡을 통과시키는 방향 아님): 11 이상 고유어 수사('서른 개')·한자어 수사
# 표기, 단위 동의어(3세대↔세 가구, 6개월↔여섯 달, 65세↔65살)는 아직 등가로
# 인정하지 못한다.
_NATIVE_NUMERALS: dict[str, int] = {
    "한": 1, "두": 2, "세": 3, "네": 4, "다섯": 5,
    "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9, "열": 10,
}
# '(?<![가-힣])'는 '동네 곳'의 '네 곳'(4곳) 같은 어중 오인을 막는다.
NATIVE_COUNT_RE = re.compile(
    r"(?<![가-힣])(다섯|여섯|일곱|여덟|아홉|한|두|세|네|열)\s*("
    + "|".join("개(?!월)" if u == "개" else u
               for u in COUNT_UNITS if u not in ("%", "퍼센트"))
    + r")"
)


def normalize_count(number_text: str, unit: str) -> str:
    """Canonicalize a count expression: '3,000'+'가구'->'3000가구', '32'+'퍼센트'->'32%'."""
    value = int(number_text.replace(",", ""))
    canonical_unit = "%" if unit in ("%", "퍼센트") else unit
    return f"{value}{canonical_unit}"


def count_values(text: str) -> set[str]:
    """모든 개수 표현의 정규값 집합 (아라비아 표기 + 고유어 수사)."""
    values: set[str] = set()
    for m in COUNT_RE.finditer(text):
        values.add(normalize_count(m.group(1), m.group(2)))
    for m in NATIVE_COUNT_RE.finditer(text):
        values.add(f"{_NATIVE_NUMERALS[m.group(1)]}{m.group(2)}")
    return values
