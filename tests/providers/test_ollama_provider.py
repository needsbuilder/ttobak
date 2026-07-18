import sys
import types


from ttobak.providers.base import LLMProvider
from ttobak.providers.ollama_provider import OllamaProvider


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


class _ChatResponse:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _FakeOllamaClient:
    """Mimics ollama.Client shape for tests — no daemon."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.last_kwargs: dict | None = None

    def chat(self, **kwargs):
        self.last_kwargs = kwargs
        return _ChatResponse(self._content)


def test_satisfies_protocol():
    assert isinstance(OllamaProvider(client=_FakeOllamaClient("ok")), LLMProvider)


def test_generate_returns_message_content():
    provider = OllamaProvider(client=_FakeOllamaClient("쉬운 글 결과입니다."))
    assert provider.generate("원문") == "쉬운 글 결과입니다."


def test_generate_passes_model_messages_and_num_predict():
    client = _FakeOllamaClient("ok")
    provider = OllamaProvider(model="qwen2.5:7b", client=client)
    provider.generate("프롬프트", system="너는 쉬운 글 변환기다", max_tokens=512)
    kwargs = client.last_kwargs
    assert kwargs["model"] == "qwen2.5:7b"
    assert kwargs["messages"] == [
        {"role": "system", "content": "너는 쉬운 글 변환기다"},
        {"role": "user", "content": "프롬프트"},
    ]
    assert kwargs["options"]["num_predict"] == 512


def test_generate_omits_system_message_when_none():
    client = _FakeOllamaClient("ok")
    provider = OllamaProvider(client=client)
    provider.generate("프롬프트")
    assert client.last_kwargs["messages"] == [
        {"role": "user", "content": "프롬프트"}
    ]


def test_default_model_is_kanana():
    provider = OllamaProvider(client=_FakeOllamaClient("ok"))
    assert provider.model == "kanana-1.5-8b"


class _RecordingClientClass:
    """Stand-in for ``ollama.Client`` that records constructor kwargs.

    Used to verify OllamaProvider passes a timeout without ever touching a
    real daemon (project rule: no live API/daemon calls in tests).
    """

    last_kwargs: dict | None = None

    def __init__(self, **kwargs) -> None:
        type(self).last_kwargs = kwargs


def _stub_ollama(monkeypatch) -> None:
    """sys.modules에 스텁 ollama 모듈을 주입한다.

    monkeypatch.setattr("ollama.Client", ...)은 실제 ollama 패키지를 import하므로
    optional extra가 없는 CI에서 ModuleNotFoundError로 죽는다 — 패키지가 없어도
    lazy-import 경로를 검증할 수 있게 모듈 자체를 스텁으로 대체한다.
    """
    _RecordingClientClass.last_kwargs = None
    stub = types.ModuleType("ollama")
    stub.Client = _RecordingClientClass
    monkeypatch.setitem(sys.modules, "ollama", stub)


def test_constructor_passes_default_timeout_to_client(monkeypatch):
    _stub_ollama(monkeypatch)
    OllamaProvider()
    assert _RecordingClientClass.last_kwargs["timeout"] == 120


def test_constructor_passes_custom_timeout_to_client(monkeypatch):
    _stub_ollama(monkeypatch)
    OllamaProvider(timeout=30)
    assert _RecordingClientClass.last_kwargs["timeout"] == 30


def test_constructor_passes_host_and_timeout_to_client(monkeypatch):
    _stub_ollama(monkeypatch)
    OllamaProvider(host="http://localhost:11434", timeout=60)
    assert _RecordingClientClass.last_kwargs["host"] == "http://localhost:11434"
    assert _RecordingClientClass.last_kwargs["timeout"] == 60


def test_explicit_client_bypasses_timeout_wiring():
    """client= 주입 시 ollama 패키지를 아예 import하지 않는 기존 계약 유지."""
    client = _FakeOllamaClient("ok")
    provider = OllamaProvider(client=client, timeout=5)
    assert provider._client is client
