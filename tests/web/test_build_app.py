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


# (2026-07-29) 스텁 모드가 화면에서 구분되지 않으면, 고정 응답을 실제 변환
# 결과로 오인할 수 있다. 검증자는 터미널이 아니라 브라우저를 보므로 stderr
# 경고만으로는 부족하다 — 배너를 UI 에도 띄운다.
def test_build_app_shows_stub_banner_when_provider_is_fake():
    blob = str(webapp.build_app(provider=_fake()).get_config_file())
    assert "데모 스텁 모드" in blob


def test_build_app_has_no_stub_banner_with_a_real_provider():
    class _Realish:
        def generate(self, prompt, *, system=None, max_tokens=2048):
            return "쉬운 글입니다."

    blob = str(webapp.build_app(provider=_Realish()).get_config_file())
    assert "데모 스텁 모드" not in blob


# Regression (#13, 2026-07-06): the pictogram "broken image" bug's real root
# cause was the missing gr.set_static_paths() wiring. Without this test, deleting
# that call passes all other web tests green while pictograms 403 again.
def test_build_app_registers_pictogram_static_path(monkeypatch):
    calls = []
    monkeypatch.setattr(gr, "set_static_paths", lambda paths: calls.append(list(paths)))
    webapp.build_app(provider=_fake())
    assert calls, "build_app must call gr.set_static_paths for the pictogram dir"
    served = [str(p) for group in calls for p in group]
    assert any(p.endswith("assets/pictograms") for p in served), (
        f"set_static_paths not called with the pictograms dir; got {served}"
    )
