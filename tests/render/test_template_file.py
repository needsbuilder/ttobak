from pathlib import Path

import ttobak

TEMPLATE = Path(ttobak.__file__).parent / "templates" / "result.html.j2"


def test_template_file_exists():
    assert TEMPLATE.is_file()


def test_template_contains_layout_and_disclaimer_literals():
    body = TEMPLATE.read_text(encoding="utf-8")
    assert "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다" in body
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
