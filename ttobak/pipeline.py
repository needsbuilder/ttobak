"""Easy-Read pipeline: GENERATE -> MEASURE -> REVISE orchestration (spec 4.2 B).

``score`` and ``verify`` are imported at module level so tests can
monkeypatch them with deterministic stubs. The revise loop only runs while the
Fidelity verdict is REVISE; HUMAN_REVIEW (e.g. a negation flip) terminates
immediately and is never auto-revised (spec 6.7, 6.8).
"""
from __future__ import annotations

from datetime import date

from ttobak.common import Verdict
from ttobak.fidelity.models import Slot
from ttobak.ir import Document
from ttobak.levels import Level
from ttobak.metric.models import Violation
from ttobak.providers.base import LLMProvider
from ttobak.result import EasyReadResult

# Module-level references for monkeypatching in tests
import ttobak.fidelity as _fidelity_module
import ttobak.metric as _metric_module

score = _metric_module.score
verify = _fidelity_module.verify

GENERATE_SYSTEM = (
    "당신은 한국어 '쉬운 정보(Easy-Read)' 변환기입니다. "
    "어려운 공공·행정 문서를 발달장애인·고령자·저문해자가 이해할 수 있게 "
    "다시 씁니다. 규칙: 한 문장에 한 가지 생각만 담고, 짧고 쉬운 단어를 쓰며, "
    "한자어·외래어·피동·이중부정을 피합니다. "
    "숫자·날짜·금액·기한·자격조건·기관명은 원문 그대로 정확히 보존합니다. "
    "원문에 없는 사실을 추가하지 않습니다. 변환된 본문만 출력합니다."
)

REVISE_SYSTEM = (
    "당신은 한국어 '쉬운 정보' 교정기입니다. 이전 변환본에서 발견된 "
    "쉬움 위반과 사실 왜곡을 고칩니다. 아래 '반드시 지킬 제약'은 "
    "글자 그대로(verbatim) 지켜야 하며, 의역·반올림·표현 약화가 금지됩니다. "
    "교정된 본문만 출력합니다."
)

_LEVEL_LABEL: dict[Level, str] = {
    Level.PLAIN: "보통 읽기(쉬운 표준 한국어, 문장은 짧게)",
    Level.EASY: "쉬운 글(Easy Korean: 한 줄 한 생각, 가장 쉬운 단어)",
}


def build_generate_prompt(source_text: str, level: Level) -> str:
    """Build the first-pass GENERATE prompt embedding the source verbatim."""
    label = _LEVEL_LABEL[level]
    return (
        f"다음 원문을 '{label}' 수준의 쉬운 정보로 변환하세요.\n\n"
        f"[원문]\n{source_text}\n\n"
        "[규칙]\n"
        "- 한 문장에 한 가지 생각만 담으세요.\n"
        "- 숫자·날짜·금액·기한·자격조건·기관명은 원문 그대로 보존하세요.\n"
        "- 원문에 없는 내용을 만들지 마세요.\n\n"
        "[변환 결과]\n"
    )


def build_revise_prompt(
    source_text: str,
    prev_easy_text: str,
    level: Level,
    violations: list[Violation],
    failed_slots: list[Slot],
) -> str:
    """Build the REVISE prompt: prior easy text + hard verbatim constraints
    from Fidelity failed slots and K-ER violations (spec section 6.8)."""
    label = _LEVEL_LABEL[level]

    if failed_slots:
        slot_lines = "\n".join(
            f"- '{s.raw_span}' (을)를 글자 그대로 포함하세요. 반올림·의역·표현 약화 금지."
            for s in failed_slots
        )
        slot_block = "[반드시 지킬 제약 — 사실 보존(verbatim)]\n" + slot_lines + "\n\n"
    else:
        slot_block = ""

    if violations:
        viol_lines = "\n".join(
            f"- [{v.severity.value}] {v.rule}: '{v.span}' → {v.suggestion}" for v in violations
        )
        viol_block = "[고칠 쉬움 위반]\n" + viol_lines + "\n\n"
    else:
        viol_block = ""

    return (
        f"이전 변환본을 '{label}' 수준에 맞게 교정하세요. "
        "아래 제약을 지키면서 더 쉽게 다시 쓰세요.\n\n"
        f"[원문]\n{source_text}\n\n"
        f"[이전 변환본 — 이것을 고치세요]\n{prev_easy_text}\n\n"
        f"{slot_block}"
        f"{viol_block}"
        "[교정 결과]\n"
    )


def _ref_date(doc: Document) -> date:
    raw = doc.meta.get("ref_date")
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str) and raw:
        return date.fromisoformat(raw)
    return date.today()


def simplify(
    doc: Document,
    level: Level,
    provider: LLMProvider,
    max_revise: int = 3,
) -> EasyReadResult:
    """Run generate->measure->revise and return an EasyReadResult."""
    ref_date = _ref_date(doc)
    source_text = doc.text()

    prompt = build_generate_prompt(source_text, level)
    easy_text = provider.generate(prompt, system=GENERATE_SYSTEM)

    ker = score(easy_text, level, source_text)
    fidelity = verify(doc, easy_text, ref_date)

    revisions = 0
    while fidelity.verdict is Verdict.REVISE and revisions < max_revise:
        revise_prompt = build_revise_prompt(
            source_text, easy_text, level, ker.violations, fidelity.failed_slots
        )
        easy_text = provider.generate(revise_prompt, system=REVISE_SYSTEM)
        revisions += 1
        ker = score(easy_text, level, source_text)
        fidelity = verify(doc, easy_text, ref_date)

    return EasyReadResult(
        source=doc,
        easy_text=easy_text,
        level=level,
        ker=ker,
        fidelity=fidelity,
        revisions=revisions,
        verdict=fidelity.verdict,
    )
