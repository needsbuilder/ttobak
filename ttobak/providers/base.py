"""The LLMProvider abstraction.

Every provider (Fake, Anthropic, Ollama, ...) implements this structural
Protocol. Callers depend only on ``generate``; the engine is provider-agnostic.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal text-in / text-out LLM interface.

    Implementations must be deterministic in tests (use FakeProvider). Real
    providers (Anthropic, Ollama) are guarded behind optional dependencies.
    """

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """Return the model's text completion for ``prompt``.

        Args:
            prompt: The user prompt (the request to the model).
            system: Optional system instruction guiding the model's behavior.
            max_tokens: Upper bound on generated tokens.

        Returns:
            The generated text as a single string.
        """
        ...
