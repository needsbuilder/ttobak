import pytest

gr = pytest.importorskip("gradio")

from ttobak.providers import FakeProvider
from ttobak.web import app as webapp


def _fake():
    return FakeProvider(default="쉬운 글입니다.")


def test_build_app_returns_blocks():
    assert isinstance(webapp.build_app(provider=_fake()), gr.Blocks)


def test_build_app_default_provider_does_not_raise(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("TTOBAK_PROVIDER", raising=False)
    assert isinstance(webapp.build_app(), gr.Blocks)


def test_build_app_contains_disclaimer():
    demo = webapp.build_app(provider=_fake())
    blob = str(demo.get_config_file())
    assert "원문이 우선" in blob
