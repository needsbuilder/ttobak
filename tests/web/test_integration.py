import pytest

from ttobak.providers import FakeProvider
from ttobak.web import app as webapp
from ttobak.web.provider import make_provider


REALISTIC_NOTICE = (
    "2026년도 국민건강보험료 고지서\n"
    "납부할 금액: 1,295,400원\n"
    "납부 기한: 2026년 7월 17일까지\n"
    "만 65세 이상 어르신은 경감 신청을 하실 수 있습니다."
)


def _fake():
    return FakeProvider(default="건강보험료는 1,295,400원입니다.\n2026년 7월 17일까지 내세요.")


def test_env_round_trip_fake(monkeypatch):
    monkeypatch.setenv("TTOBAK_PROVIDER", "fake")
    assert isinstance(make_provider(), FakeProvider)


def test_end_to_end_handler_via_fakeprovider():
    html, ker_badge, fid_badge = webapp.simplify_handler(
        REALISTIC_NOTICE, None, next(iter(webapp.LEVEL_CHOICES)), _fake())
    assert html.strip()
    assert "K-ER" in ker_badge
    assert fid_badge.strip()


def test_build_app_then_handler_share_provider():
    gr = pytest.importorskip("gradio")
    provider = _fake()
    demo = webapp.build_app(provider=provider)
    assert isinstance(demo, gr.Blocks)
    html, _, _ = webapp.simplify_handler(
        REALISTIC_NOTICE, None, next(iter(webapp.LEVEL_CHOICES)), provider)
    assert "<" in html
