from ttobak.prompts import (
    EASY_READ_SYSTEM,
    build_generate_prompt,
    build_revise_prompt,
)
from ttobak.levels import Level
from ttobak.common import Severity
from ttobak.metric.models import Violation
from ttobak.fidelity.models import Slot, SlotType


SOURCE = "건강보험료 1,295,400원을 2026년 7월 17일까지 납부하여야 합니다."


def test_system_prompt_states_fidelity_first():
    assert "원문" in EASY_READ_SYSTEM
    assert "쉬운" in EASY_READ_SYSTEM


def test_generate_prompt_contains_source_and_level_easy():
    prompt = build_generate_prompt(SOURCE, Level.EASY)
    assert SOURCE in prompt
    assert "쉬운 글" in prompt  # Level.EASY label


def test_generate_prompt_level_plain_uses_plain_label():
    prompt = build_generate_prompt(SOURCE, Level.PLAIN)
    assert "보통 읽기" in prompt
    assert SOURCE in prompt


def test_revise_prompt_injects_failed_slot_verbatim_and_violation():
    failed = [
        Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY),
        Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE),
    ]
    violations = [
        Violation(
            rule="sentence_length",
            span="건강보험료를 ... 납부하여야 합니다",
            severity=Severity.MED,
            suggestion="문장을 두 개로 나누세요.",
        )
    ]
    prompt = build_revise_prompt(
        SOURCE, Level.EASY, "건강보험료 약 130만 원을 7월에 내세요.", violations, failed
    )
    assert "1,295,400원" in prompt
    assert "2026년 7월 17일" in prompt
    assert "의역 금지" in prompt
    assert "sentence_length" in prompt
    assert "문장을 두 개로 나누세요." in prompt
    assert "건강보험료 약 130만 원을 7월에 내세요." in prompt


def test_revise_prompt_omits_empty_constraint_sections():
    prompt = build_revise_prompt(SOURCE, Level.EASY, "이전 글.", [], [])
    assert "반드시 원문 그대로" not in prompt
    assert "쉬움 규칙 위반" not in prompt
    assert "[고친 쉬운 글]" in prompt
