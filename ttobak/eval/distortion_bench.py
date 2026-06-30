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
