
from ttobak.providers.anthropic_provider import AnthropicProvider
from ttobak.providers.base import LLMProvider


class _Block:
    def __init__(self, type_: str, text: str) -> None:
        self.type = type_
        self.text = text


class _Response:
    def __init__(self, blocks):
        self.content = blocks


class _Messages:
    def __init__(self, response):
        self._response = response
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeAnthropicClient:
    """Mimics anthropic.Anthropic() shape for tests — no network."""

    def __init__(self, response):
        self.messages = _Messages(response)


def test_satisfies_protocol():
    client = _FakeAnthropicClient(_Response([_Block("text", "쉬운 글입니다.")]))
    assert isinstance(AnthropicProvider(client=client), LLMProvider)


def test_generate_returns_concatenated_text_blocks():
    client = _FakeAnthropicClient(
        _Response([_Block("text", "첫 줄입니다.\n"), _Block("text", "둘째 줄입니다.")])
    )
    provider = AnthropicProvider(client=client)
    out = provider.generate("이 문장을 쉽게 바꿔주세요.")
    assert out == "첫 줄입니다.\n둘째 줄입니다."


def test_generate_skips_non_text_blocks():
    client = _FakeAnthropicClient(
        _Response([_Block("thinking", "내부 추론"), _Block("text", "최종 답")])
    )
    provider = AnthropicProvider(client=client)
    assert provider.generate("프롬프트") == "최종 답"


def test_generate_passes_model_system_and_max_tokens():
    client = _FakeAnthropicClient(_Response([_Block("text", "ok")]))
    provider = AnthropicProvider(model="claude-opus-4-8", client=client)
    provider.generate("프롬프트", system="너는 쉬운 글 변환기다", max_tokens=512)
    kwargs = client.messages.last_kwargs
    assert kwargs["model"] == "claude-opus-4-8"
    assert kwargs["max_tokens"] == 512
    assert kwargs["system"] == "너는 쉬운 글 변환기다"
    assert kwargs["messages"] == [{"role": "user", "content": "프롬프트"}]


def test_generate_omits_system_when_none():
    client = _FakeAnthropicClient(_Response([_Block("text", "ok")]))
    provider = AnthropicProvider(client=client)
    provider.generate("프롬프트")
    assert "system" not in client.messages.last_kwargs
