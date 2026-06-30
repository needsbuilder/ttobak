from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ttobak.common import Verdict
from ttobak.result import EasyReadResult

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_TEMPLATE_NAME = "result.html.j2"

# Always-on disclaimer (spec 3.1 / 8.7). Must contain the verbatim phrase the
# template test asserts: "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다".
_DISCLAIMER = "이 쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다. 자동 변환 결과입니다."

_KER_UNVALIDATED_NOTE = (
    "이 점수는 한국 쉬운 정보 지침에 정렬된 규칙 기반 루브릭이며, "
    "경험적으로 검증된 점수가 아닙니다. 규칙별 위반 목록을 함께 확인하세요."
)

_VERDICT_BADGE: dict[Verdict, tuple[str, str]] = {
    Verdict.PASS: ("pass", "통과"),
    Verdict.REVISE: ("revise", "수정 필요"),
    Verdict.HUMAN_REVIEW: ("human_review", "검수 필요"),
}

_LEVEL_LABEL = {"plain": "보통 읽기", "easy": "쉬운 글"}

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_html(result: EasyReadResult) -> str:
    """Render an EasyReadResult to side-by-side accessible HTML.

    Always includes the source text, the easy text, the Fidelity-first
    disclaimer, the (non-validated) K-ER score + per-rule violations, the
    fidelity verdict badge, and pictograms as file-path references only.
    """
    badge_class, badge_label = _VERDICT_BADGE[result.fidelity.verdict]
    template = _env.get_template(_TEMPLATE_NAME)
    return template.render(
        disclaimer=_DISCLAIMER,
        source_text=result.source.text(),
        easy_text=result.easy_text,
        level_label=_LEVEL_LABEL.get(result.level.value, result.level.value),
        ker_score=int(round(result.ker.score)),
        ker_unvalidated_note=_KER_UNVALIDATED_NOTE,
        violations=[
            {"rule": v.rule, "span": v.span, "severity": v.severity.value, "suggestion": v.suggestion}
            for v in result.ker.violations
        ],
        fidelity_verdict=result.fidelity.verdict.value,
        fidelity_badge_class=badge_class,
        fidelity_badge_label=badge_label,
        pictograms=[{"glyph_id": p.glyph_id, "caption": p.caption} for p in result.pictograms],
    )
