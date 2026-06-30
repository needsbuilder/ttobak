import re
from pathlib import Path

import jinja2
import ttobak

TEMPLATE = Path(ttobak.__file__).parent / "templates" / "result.html.j2"

_DISCLAIMER_TEXT = "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다"

# Minimal context for rendering the template in tests.
_MINIMAL_CTX: dict = {
    "disclaimer": "",
    "ker_score": 80,
    "level_label": "중급",
    "fidelity_badge_class": "pass",
    "fidelity_badge_label": "통과",
    "source_text": "원문 내용",
    "easy_text": "쉬운 글 내용",
    "pictograms": [],
    "violations": [],
    "ker_unvalidated_note": "참고용",
}


def _render(ctx: dict | None = None) -> str:
    """Render the template with the given context (defaults to minimal)."""
    loader = jinja2.FileSystemLoader(str(TEMPLATE.parent))
    env = jinja2.Environment(loader=loader, autoescape=True)
    tmpl = env.get_template(TEMPLATE.name)
    return tmpl.render(**(ctx or _MINIMAL_CTX))


def test_template_file_exists():
    assert TEMPLATE.is_file()


def test_template_contains_layout_and_disclaimer_literals():
    body = TEMPLATE.read_text(encoding="utf-8")
    assert _DISCLAIMER_TEXT in body
    assert "font-size: 18px" in body
    assert "text-align: left" in body
    assert "규칙 기반 루브릭" in body
    assert 'class="source"' in body
    assert 'class="easy"' in body


def test_template_references_expected_variables():
    body = TEMPLATE.read_text(encoding="utf-8")
    for var in ("source_text", "easy_text", "ker_score", "violations",
                "fidelity_badge_label", "pictograms", "disclaimer"):
        assert var in body


def test_disclaimer_visible_in_rendered_output_when_variable_empty():
    """Disclaimer text must appear in the rendered visible HTML even when
    the caller passes an empty disclaimer string (regression for false-negative)."""
    rendered = _render(_MINIMAL_CTX | {"disclaimer": ""})
    # Extract just the disclaimer div, not the HTML comment
    match = re.search(
        r'<div[^>]*class="disclaimer"[^>]*>(.*?)</div>',
        rendered,
        re.DOTALL,
    )
    assert match is not None, "disclaimer div not found in rendered output"
    div_content = match.group(1)
    assert _DISCLAIMER_TEXT in div_content, (
        f"Disclaimer text not visible inside <div class='disclaimer'>: {div_content!r}"
    )


def test_disclaimer_visible_in_rendered_output_when_variable_provided():
    """When caller provides a full disclaimer string, that text is shown."""
    custom = "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다. 자동 변환 결과입니다."
    rendered = _render(_MINIMAL_CTX | {"disclaimer": custom})
    match = re.search(
        r'<div[^>]*class="disclaimer"[^>]*>(.*?)</div>',
        rendered,
        re.DOTALL,
    )
    assert match is not None, "disclaimer div not found in rendered output"
    div_content = match.group(1)
    assert custom in div_content, (
        f"Custom disclaimer not visible inside <div class='disclaimer'>: {div_content!r}"
    )
