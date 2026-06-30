"""Prompt builders for the GENERATE and REVISE steps of the pipeline.

Pure string assembly — no LLM call here. The pipeline injects K-ER
violations and Fidelity failed slots into the REVISE prompt as hard,
verbatim-preserving constraints (spec section 6.8).
"""
from __future__ import annotations

from ttobak.fidelity.models import Slot
from ttobak.levels import Level
from ttobak.metric.models import Violation

EASY_READ_SYSTEM = (
    "당신은 한국어 '쉬운 정보(Easy-Read)' 변환기입니다. "
    "어려운 공공·행정 문서를 누구나 이해할 수 있는 쉬운 한국어로 바꿉니다. "
    "규칙: 한 문장에 한 가지 내용만 담고, 짧고 능동적인 문장을 쓰며, "
    "어려운 한자어·전문어를 쉬운 말로 풀어 씁니다. "
    "가장 중요한 원칙: 숫자·날짜·금액·기한·자격·기관명을 절대 바꾸지 말고 "
    "원문 그대로 보존합니다. 사실이 흐려지면 안 됩니다. "
    "쉬운 글로 바꾼 본문만 출력하고, 설명이나 머리말은 붙이지 마세요."
)

_LEVEL_LABEL = {
    Level.PLAIN: "보통 읽기(쉬운 한국어, 텍스트 중심)",
    Level.EASY: "쉬운 글(쉬운 한국어, 한 줄 한 생각, 그림 친화)",
}


def build_generate_prompt(source_text: str, level: Level) -> str:
    """Build the first-pass GENERATE prompt for the given output level."""
    return (
        f"다음 원문을 '{_LEVEL_LABEL[level]}' 등급의 쉬운 정보로 바꾸세요.\n"
        "숫자·날짜·금액·기한·자격·기관명은 원문 그대로 유지하세요.\n\n"
        f"[원문]\n{source_text}\n\n"
        "[쉬운 글]\n"
    )


def build_revise_prompt(
    source_text: str,
    level: Level,
    previous_easy: str,
    violations: list[Violation],
    failed_slots: list[Slot],
) -> str:
    """Build the REVISE prompt, injecting violations and failed slots as hard constraints."""
    lines: list[str] = [
        f"앞서 만든 '쉬운 글'을 아래 지적사항에 맞게 고치세요. "
        f"등급은 '{_LEVEL_LABEL[level]}'입니다.",
        "",
        "[원문]",
        source_text,
        "",
        "[이전 쉬운 글]",
        previous_easy,
        "",
    ]
    if failed_slots:
        lines.append("[반드시 원문 그대로 포함해야 하는 표현 — 의역 금지]")
        for slot in failed_slots:
            lines.append(f"- \"{slot.raw_span}\" (정확히 이 문자열을 그대로 쓰세요)")
        lines.append("")
    if violations:
        lines.append("[쉬움 규칙 위반 — 고칠 것]")
        for v in violations:
            lines.append(f"- [{v.rule}] \"{v.span}\": {v.suggestion}")
        lines.append("")
    lines.append("[고친 쉬운 글]")
    return "\n".join(lines)
