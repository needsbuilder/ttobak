from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Callable

from pydantic import BaseModel


class DistortionType(str, Enum):
    """Injected-distortion taxonomy (spec 6.9). 10 distortions + clean control."""

    NUMBER_SWAP = "number_swap"            # 30,000 -> 3,000
    DIGIT_DROP = "digit_drop"              # 1,295,400 -> 129,540
    KRW_UNIT_ERROR = "krw_unit_error"      # 3억 -> 3천만
    DATE_SHIFT = "date_shift"              # 7/17 -> 7/7
    INCLUSIVITY_FLIP = "inclusivity_flip"  # 까지 -> 전에
    NEGATION_DROP = "negation_drop"        # 제외 -> 포함
    CONDITION_FLIP = "condition_flip"      # 만 65세 이상 -> 이하
    RANGE_WEAKEN = "range_weaken"          # 미만 -> 이하
    ENTITY_SWAP = "entity_swap"            # 강서구청 -> 송파구청
    HALLUCINATED_ENTITY = "hallucinated_entity"  # add unsourced entity
    CLEAN = "clean"                        # faithful control, must PASS


class DistortionCase(BaseModel):
    case_id: str
    source_text: str
    easy_text: str
    distorted_text: str
    distortion_type: DistortionType
    is_clean: bool
    expected_pass: bool


def _number_swap(text: str) -> str | None:
    return text.replace("30,000", "3,000", 1) if "30,000" in text else None

def _digit_drop(text: str) -> str | None:
    return text.replace("1,295,400", "129,540", 1) if "1,295,400" in text else None

def _krw_unit_error(text: str) -> str | None:
    return text.replace("3억", "3천만", 1) if "3억" in text else None

def _date_shift(text: str) -> str | None:
    return text.replace("7월 17일", "7월 7일", 1) if "7월 17일" in text else None

def _inclusivity_flip(text: str) -> str | None:
    return text.replace("까지", " 전에", 1) if "까지" in text else None

def _negation_drop(text: str) -> str | None:
    if "빠집니다" in text:
        return text.replace("빠집니다", "포함됩니다", 1)
    if "제외됩니다" in text:
        return text.replace("제외됩니다", "포함됩니다", 1)
    return None

def _condition_flip(text: str) -> str | None:
    return text.replace("이상", "이하", 1) if "이상" in text else None

def _range_weaken(text: str) -> str | None:
    return text.replace("미만", "이하", 1) if "미만" in text else None

def _entity_swap(text: str) -> str | None:
    return text.replace("강서구청", "송파구청", 1) if "강서구청" in text else None

def _hallucinated_entity(text: str) -> str | None:
    if "국민건강보험공단" in text:
        return None
    return text + " 자세한 내용은 국민건강보험공단에 문의하세요."


_DISTORTERS: dict[DistortionType, Callable[[str], "str | None"]] = {
    DistortionType.NUMBER_SWAP: _number_swap,
    DistortionType.DIGIT_DROP: _digit_drop,
    DistortionType.KRW_UNIT_ERROR: _krw_unit_error,
    DistortionType.DATE_SHIFT: _date_shift,
    DistortionType.INCLUSIVITY_FLIP: _inclusivity_flip,
    DistortionType.NEGATION_DROP: _negation_drop,
    DistortionType.CONDITION_FLIP: _condition_flip,
    DistortionType.RANGE_WEAKEN: _range_weaken,
    DistortionType.ENTITY_SWAP: _entity_swap,
    DistortionType.HALLUCINATED_ENTITY: _hallucinated_entity,
}


def generate_distortions(source_text: str, easy_text: str, *, ref_date: date, seed: int = 0) -> list[DistortionCase]:
    """Emit labeled DistortionCases for one faithful (source, easy) pair (spec 6.9).

    One case per realizable distortion type (skipped if its trigger pattern is
    absent from easy_text) plus exactly one CLEAN control. Deterministic: cases
    are emitted in stable DistortionType declaration order; ``seed`` namespaces case_ids.
    """
    cases: list[DistortionCase] = []
    for dtype in DistortionType:
        if dtype is DistortionType.CLEAN:
            continue
        mutated = _DISTORTERS[dtype](easy_text)
        if mutated is None or mutated == easy_text:
            continue
        cases.append(DistortionCase(
            case_id=f"{seed}-{dtype.value}", source_text=source_text, easy_text=easy_text,
            distorted_text=mutated, distortion_type=dtype, is_clean=False, expected_pass=False))
    cases.append(DistortionCase(
        case_id=f"{seed}-clean", source_text=source_text, easy_text=easy_text,
        distorted_text=easy_text, distortion_type=DistortionType.CLEAN, is_clean=True, expected_pass=True))
    return cases
