from ttobak.common import Severity, Verdict
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Block, BlockType, Document
from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation
from ttobak.pictogram.models import PictogramRef
from ttobak.render import render_html
from ttobak.result import EasyReadResult


def _build_result() -> EasyReadResult:
    source = Document(
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="2026년 7월분 보험료 1,295,400원을 2026년 7월 25일까지 납부하시기 바랍니다."),
        ],
        source_mime="text/plain",
    )
    ker = KERReport(
        score=81.0, level_estimate=2, sub_scores={"rule": 81.0},
        violations=[Violation(rule="한자어", span="납부", severity=Severity.MED, suggestion="'돈을 내요'로 바꾸기")],
    )
    fidelity = FidelityReport(slots=[], verdict=Verdict.PASS)
    return EasyReadResult(
        source=source,
        easy_text="2026년 7월 보험료는 1,295,400원입니다.\n2026년 7월 25일까지 돈을 내세요.",
        level=Level.EASY, ker=ker, fidelity=fidelity,
        pictograms=[PictogramRef(concept="돈", set="mulberry", glyph_id="mulberry/money.svg", caption="돈")],
        revisions=1, verdict=Verdict.PASS,
    )


def test_render_html_returns_str():
    html = render_html(_build_result())
    assert isinstance(html, str)
    assert html.lstrip().startswith("<!DOCTYPE html>")


def test_render_html_contains_both_texts():
    html = render_html(_build_result())
    assert "건강보험료 납부 안내" in html
    assert "2026년 7월 25일까지 돈을 내세요" in html


def test_render_html_always_has_disclaimer():
    assert "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다" in render_html(_build_result())


def test_render_html_shows_score_and_violation():
    html = render_html(_build_result())
    assert "81" in html
    assert "규칙 기반 루브릭" in html
    assert "한자어" in html
    assert "돈을 내요" in html


def test_render_html_fidelity_badge_pass():
    html = render_html(_build_result())
    assert "badge-pass" in html
    assert "통과" in html


def test_render_html_renders_pictogram_path_not_inlined():
    html = render_html(_build_result())
    assert 'src="mulberry/money.svg"' in html
    assert "data:image" not in html


def test_render_html_human_review_badge():
    result = _build_result()
    result.verdict = Verdict.HUMAN_REVIEW
    result.fidelity = FidelityReport(slots=[], verdict=Verdict.HUMAN_REVIEW)
    html = render_html(result)
    assert "badge-human_review" in html
    assert "검수 필요" in html


def test_render_html_easy_layout_font_size():
    html = render_html(_build_result())
    assert "font-size: 18px" in html
    assert "text-align: left" in html
