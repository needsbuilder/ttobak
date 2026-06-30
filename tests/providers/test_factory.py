import pytest

from ttobak.providers import (
    AnthropicProvider,
    FakeProvider,
    LLMProvider,
    OllamaProvider,
    get_provider,
)


def test_get_provider_fake_returns_fakeprovider():
    provider = get_provider("fake", responses=["쉬운 글"])
    assert isinstance(provider, FakeProvider)
    assert isinstance(provider, LLMProvider)
    assert provider.generate("원문") == "쉬운 글"


def test_get_provider_is_case_insensitive():
    assert isinstance(get_provider("FAKE", responses=["x"]), FakeProvider)


def test_get_provider_anthropic_passes_kwargs():
    # Inject a passthrough client so no anthropic SDK / API key is needed.
    provider = get_provider("anthropic", client=object(), model="claude-opus-4-8")
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-opus-4-8"


def test_get_provider_ollama_passes_kwargs():
    provider = get_provider("ollama", client=object(), model="qwen2.5:7b")
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "qwen2.5:7b"


def test_get_provider_unknown_raises_valueerror():
    with pytest.raises(ValueError, match="unknown provider"):
        get_provider("gpt-imaginary")
