"""Anthropic (Claude) provider — the demo default.

The ``anthropic`` SDK is an optional dependency, imported lazily at
construction so importing this module never fails when the SDK is absent.
Tests inject a stand-in ``client`` and never touch a live API or key.
"""

from __future__ import annotations


class AnthropicProvider:
    """LLMProvider backed by the Anthropic Messages API.

    Args:
        model: Claude model id. Default ``claude-opus-4-8``.
        api_key: Optional explicit API key. If ``None``, the SDK resolves it
            from the environment (``ANTHROPIC_API_KEY``).
        client: Optional pre-built client (used by tests to avoid the network).
            When provided, the ``anthropic`` SDK is never imported.
    """

    def __init__(
        self,
        *,
        model: str = "claude-opus-4-8",
        api_key: str | None = None,
        client: object | None = None,
    ) -> None:
        self.model = model
        if client is not None:
            self._client = client
            return
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise ImportError(
                "AnthropicProvider requires the 'anthropic' package. "
                "Install it with: pip install 'ttobak[anthropic]'"
            ) from exc
        self._client = (
            anthropic.Anthropic(api_key=api_key)
            if api_key is not None
            else anthropic.Anthropic()
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        return "".join(
            block.text for block in response.content if block.type == "text"
        )
