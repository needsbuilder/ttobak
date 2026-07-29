import ttobak.web.provider as provider_mod
from ttobak.providers import FakeProvider
from ttobak.web import provider as _alias  # noqa: F401 — 기존 import 경로 유지


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


# ---------------------------------------------------------------------------
# 대회 운영규정 제9조 ②-1-다 대응 (2026-07-29)
#
# "외부 API 호출을 통해서만 작동하는 상용 API 전용 모델을 서비스 형태로 단순
# 연결하는 출품작은 제한한다." 또박은 로컬 Ollama(Qwen2.5-7B / Kanana-1.5-8B,
# 모두 Apache-2.0)로 독립 구동되며, 원격 Anthropic 은 선택적 대안이다.
# 그 사실이 문서 문구가 아니라 **코드의 기본 동작**으로 드러나야 한다.
# ---------------------------------------------------------------------------


def test_default_provider_is_local_ollama():
    """기본 프로바이더는 로컬 독립 구동(ollama)이어야 한다 — 원격 API 아님."""
    assert provider_mod.DEFAULT_PROVIDER == "ollama"


def test_none_without_env_takes_the_ollama_path(monkeypatch):
    """이름·환경변수 모두 없으면 ollama 경로를 탄다(생성자 호출로 확인)."""
    monkeypatch.delenv("TTOBAK_PROVIDER", raising=False)
    built = []

    class _StubOllama:
        def __init__(self, **kwargs):
            built.append(kwargs)

        def generate(self, prompt, *, system=None, max_tokens=2048):
            return "stub"

    monkeypatch.setattr(provider_mod, "OllamaProvider", _StubOllama)
    p = provider_mod.make_provider(None)
    assert built, "make_provider(None) must construct OllamaProvider"
    assert isinstance(p, _StubOllama)


def test_ollama_construction_failure_falls_back_to_fake(monkeypatch):
    """ollama 패키지·데몬이 없어도 데모는 죽지 않는다(CI 안전성)."""
    def _boom(**kwargs):
        raise ImportError("no ollama package")

    monkeypatch.setattr(provider_mod, "OllamaProvider", _boom)
    assert isinstance(provider_mod.make_provider("ollama"), FakeProvider)


def test_fallback_to_fake_warns_loudly_on_stderr(monkeypatch, capsys):
    """조용한 폴백 금지 — 스텁 응답을 실제 변환으로 오인하면 안 된다.

    (2026-07-29) 기능테스트에서 검증자가 키·데몬 없이 실행했을 때 고정 문장이
    실제 모델 출력처럼 보이는 것이 가장 큰 위험이었다.
    """
    def _boom(**kwargs):
        raise RuntimeError("daemon down")

    monkeypatch.setattr(provider_mod, "OllamaProvider", _boom)
    provider_mod.make_provider("ollama")
    err = capsys.readouterr().err
    assert "ollama" in err
    assert "고정 응답" in err or "스텁" in err


def test_unknown_provider_name_also_warns(monkeypatch, capsys):
    """오타난 이름이 조용히 스텁으로 떨어지지 않는다."""
    provider_mod.make_provider("gpt-4o")
    err = capsys.readouterr().err
    assert "gpt-4o" in err


def test_explicit_fake_does_not_warn(capsys):
    """의도적으로 fake 를 고른 경우(테스트·CI)는 경고하지 않는다."""
    provider_mod.make_provider("fake")
    assert capsys.readouterr().err == ""
