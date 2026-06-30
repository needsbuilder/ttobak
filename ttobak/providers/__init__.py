"""LLM provider abstraction for Ttobak.

Public API:
    LLMProvider        — the structural Protocol all providers satisfy.
    FakeProvider       — deterministic scripted provider for tests.
    AnthropicProvider  — Claude provider (demo default).
    OllamaProvider     — local provider (Kanana-1.5-8B / Qwen2.5).
    get_provider       — factory selecting a provider by name.
"""

from __future__ import annotations

from ttobak.providers.anthropic_provider import AnthropicProvider
from ttobak.providers.base import LLMProvider
from ttobak.providers.fake import FakeProvider
from ttobak.providers.ollama_provider import OllamaProvider

__all__ = [
    "LLMProvider",
    "FakeProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "get_provider",
]


def get_provider(name: str, **kwargs) -> LLMProvider:
    """Build a provider by name.

    Args:
        name: One of ``"fake"``, ``"anthropic"``, ``"ollama"`` (case-insensitive).
        **kwargs: Forwarded to the selected provider's constructor.

    Returns:
        A constructed LLMProvider.

    Raises:
        ValueError: If ``name`` is not a known provider.
    """
    key = name.strip().lower()
    if key == "fake":
        return FakeProvider(**kwargs)
    if key == "anthropic":
        return AnthropicProvider(**kwargs)
    if key == "ollama":
        return OllamaProvider(**kwargs)
    raise ValueError(
        f"unknown provider {name!r}; expected one of 'fake', 'anthropic', 'ollama'"
    )
