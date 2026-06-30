from ttobak.providers import FakeProvider
from ttobak.web import provider as provider_mod


def test_explicit_fake_returns_fakeprovider():
    assert isinstance(provider_mod.make_provider("fake"), FakeProvider)


def test_default_env_name_constant():
    assert provider_mod.DEFAULT_PROVIDER_ENV == "TTOBAK_PROVIDER"


def test_none_reads_env(monkeypatch):
    monkeypatch.setenv("TTOBAK_PROVIDER", "fake")
    assert isinstance(provider_mod.make_provider(None), FakeProvider)


def test_anthropic_without_key_falls_back_to_fake(monkeypatch):
    monkeypatch.delenv("TTOBAK_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    p = provider_mod.make_provider("anthropic")
    assert isinstance(p, FakeProvider)


def test_returned_provider_is_callable():
    p = provider_mod.make_provider("fake")
    out = p.generate("안녕하세요", system=None, max_tokens=64)
    assert isinstance(out, str)
