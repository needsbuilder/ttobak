
from ttobak.common import Verdict
from ttobak.providers import FakeProvider
from ttobak.web import app as webapp


def _fake():
    # default-backed so the revise loop never exhausts the queue
    return FakeProvider(default="건강보험료는 1,295,400원입니다.\n2026년 7월 17일까지 내세요.")


def test_handler_returns_three_strings_from_text():
    html, ker_badge, fid_badge = webapp.simplify_handler(
        "만 65세 이상 어르신은 2026년 7월 17일까지 신청하셔야 합니다.", None,
        next(iter(webapp.LEVEL_CHOICES)), _fake(),
    )
    assert isinstance(html, str) and html.strip()
    assert "<" in html and ">" in html
    # The renderer MUST always include the '원문 우선' disclaimer (spec 3.1 / 8.7).
    assert "원문이 우선" in html, "render_html must embed the source-precedence disclaimer"
    # The source text must appear in the rendered side-by-side view.
    assert "어르신" in html, "render_html must embed the source text"
    assert isinstance(ker_badge, str) and "K-ER" in ker_badge
    assert isinstance(fid_badge, str) and fid_badge.strip()


def test_handler_fidelity_badge_reflects_verdict():
    _, _, fid_badge = webapp.simplify_handler(
        "국민건강보험료 1,295,400원을 납부하세요.", None,
        next(iter(webapp.LEVEL_CHOICES)), _fake(),
    )
    assert any(tok in fid_badge for tok in ("통과", "검수", "재교정"))


def test_handler_empty_input_returns_error_html_not_raise():
    html, ker_badge, fid_badge = webapp.simplify_handler("", None, "쉬운 글", _fake())
    assert "오류" in html or "입력" in html
    assert ker_badge == ""
    assert fid_badge == ""


def test_ker_badge_contains_score():
    from ttobak.metric.models import KERReport
    ker = KERReport(score=81.0, level_estimate=2, sub_scores={"rule": 81.0}, violations=[])
    badge = webapp._ker_badge(ker)
    assert "81" in badge
    assert "K-ER" in badge


def test_fidelity_badge_pass_vs_human_review():
    pass_badge = webapp._fidelity_badge(Verdict.PASS)
    human_badge = webapp._fidelity_badge(Verdict.HUMAN_REVIEW)
    assert pass_badge != human_badge
    assert "검수" in human_badge


# Bug regression (2026-07-06): render_html()'s plain "assets/pictograms/..."
# src never resolves inside Gradio's gr.HTML() sandbox (broken image icon).
# The web layer must rewrite it to Gradio's /gradio_api/file= serving scheme.
def test_serve_pictograms_via_gradio_rewrites_src_to_gradio_file_scheme():
    html = '<img src="assets/pictograms/mulberry/money.svg" alt="돈">'
    rewritten = webapp._serve_pictograms_via_gradio(html)
    assert 'src="assets/pictograms/' not in rewritten
    assert rewritten.startswith(f'<img src="/gradio_api/file={webapp._PICTOGRAMS_DIR}/mulberry/money.svg"')


def test_handler_output_pictogram_src_is_gradio_servable():
    # Provider output deliberately contains pictogram-triggering concepts
    # (전화·신청) so a pictogram is GUARANTEED and the format assertion below is
    # never vacuous — #12 regression: the old test hid the format check behind
    # `if "/gradio_api/file=" in html`, which silently died if the fixture text
    # stopped matching a lexicon keyword.
    provider = FakeProvider(default="전화로 신청하세요.")
    html, _, _ = webapp.simplify_handler(
        "만 65세 이상 어르신은 2026년 7월 17일까지 신청하셔야 합니다.", None,
        next(iter(webapp.LEVEL_CHOICES)), provider,
    )
    assert 'src="assets/pictograms/' not in html, "raw core path leaked into Gradio HTML unrewritten"
    assert "/gradio_api/file=" in html, "pictogram present but not rewritten to Gradio serving scheme"
    assert str(webapp._PICTOGRAMS_DIR) in html
