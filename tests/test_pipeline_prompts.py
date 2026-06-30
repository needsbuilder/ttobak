from ttobak.levels import Level
from ttobak.common import Severity
from ttobak.metric.models import Violation
from ttobak.fidelity.models import Slot, SlotType
from ttobak.pipeline import (
    GENERATE_SYSTEM,
    REVISE_SYSTEM,
    build_generate_prompt,
    build_revise_prompt,
)


def test_build_generate_prompt_includes_source_and_level_label():
    src = "본인부담금은 1,295,400원이며 2026년 7월 17일까지 납부하셔야 합니다."
    prompt = build_generate_prompt(src, Level.EASY)
    assert src in prompt
    assert "쉬운 글" in prompt
    assert isinstance(GENERATE_SYSTEM, str) and len(GENERATE_SYSTEM) > 0


def test_build_generate_prompt_plain_level_label():
    prompt = build_generate_prompt("안내문입니다.", Level.PLAIN)
    assert "보통 읽기" in prompt


def test_build_revise_prompt_injects_failed_slots_verbatim():
    failed = [
        Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY, criticality=Severity.HIGH),
        Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE, criticality=Severity.HIGH),
    ]
    violations = [
        Violation(rule="sentence_length", span="본인부담금은 ... 납부하셔야 합니다",
                  severity=Severity.MED, suggestion="문장을 두 개로 나누세요.")
    ]
    prompt = build_revise_prompt(
        source_text="원문 텍스트", prev_easy_text="본인부담금은 약 130만 원입니다.",
        level=Level.EASY, violations=violations, failed_slots=failed,
    )
    assert "1,295,400원" in prompt
    assert "2026년 7월 17일" in prompt
    assert "본인부담금은 약 130만 원입니다." in prompt
    assert "sentence_length" in prompt
    assert "문장을 두 개로 나누세요." in prompt
    assert "그대로" in prompt
    assert isinstance(REVISE_SYSTEM, str) and len(REVISE_SYSTEM) > 0


def test_build_revise_prompt_with_no_failures_is_still_valid():
    prompt = build_revise_prompt(source_text="원문", prev_easy_text="쉬운 본문",
                                 level=Level.PLAIN, violations=[], failed_slots=[])
    assert "쉬운 본문" in prompt
    assert "원문" in prompt
