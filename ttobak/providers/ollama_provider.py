"""Ollama provider — the local fallback.

Default local model: Kanana-1.5-8B (Kakao, Apache-2.0, strong Korean).
Documented secondary: Qwen2.5-7B / 14B (Apache-2.0) via ``model="qwen2.5:7b"``.

The ``ollama`` package is an optional dependency, imported lazily at
construction. Tests inject a stand-in ``client`` and never touch a daemon.
"""

from __future__ import annotations


class OllamaProvider:
    """LLMProvider backed by a local Ollama daemon.

    Args:
        model: Ollama model tag. Default ``kanana-1.5-8b``. Documented
            alternative: ``qwen2.5:7b`` / ``qwen2.5:14b`` (Apache-2.0).
        host: Optional Ollama host URL (e.g. ``http://localhost:11434``).
            If ``None``, the client resolves it from the environment.
        client: Optional pre-built ``ollama.Client`` (used by tests to avoid
            the daemon). When provided, the ``ollama`` package is never imported.
    """

    def __init__(
        self,
        *,
        model: str = "kanana-1.5-8b",
        host: str | None = None,
        client: object | None = None,
    ) -> None:
        self.model = model
        if client is not None:
            self._client = client
            return
        try:
            from ollama import Client
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise ImportError(
                "OllamaProvider requires the 'ollama' package. "
                "Install it with: pip install 'ttobak[ollama]'"
            ) from exc
        self._client = Client(host=host) if host is not None else Client()

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        messages: list[dict] = []
        if system is not None:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        response = self._client.chat(
            model=self.model,
            messages=messages,
            options={"num_predict": max_tokens},
        )
        return response.message.content
