import pytest

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
