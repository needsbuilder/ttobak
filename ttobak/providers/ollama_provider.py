"""Ollama provider — the default. Runs entirely on the local machine.

This is what makes Ttobak independently runnable with no network and no
commercial API: the pipeline's only model dependency is an open-weight model
you download and serve yourself.

Default local model: Qwen2.5-7B (Alibaba, Apache-2.0) — pulled with
``ollama pull qwen2.5:7b``. Chosen as the default because it is in Ollama's
official library, so a first-time run works with no extra setup. Qwen2.5's
3B and 72B sizes are NC (Qwen Research License) and must not be used; 7B/14B
are Apache-2.0.

Documented alternative: Kanana-1.5 (Kakao, Apache-2.0, strong Korean). It is
**not** in Ollama's official library, so it needs a Hugging Face GGUF tag
(``model="hf.co/<repo>-GGUF:<quant>"``) rather than a bare name.

The ``ollama`` package is an optional dependency, imported lazily at
construction. Tests inject a stand-in ``client`` and never touch a daemon.
"""

from __future__ import annotations


class OllamaProvider:
    """LLMProvider backed by a local Ollama daemon.

    Args:
        model: Ollama model tag. Default ``qwen2.5:7b`` (Apache-2.0, in the
            official library). Also fine: ``qwen2.5:14b``. Kanana-1.5 needs a
            Hugging Face GGUF tag — see the module docstring.
        host: Optional Ollama host URL (e.g. ``http://localhost:11434``).
            If ``None``, the client resolves it from the environment.
        timeout: Request timeout in seconds passed to ``ollama.Client``.
            Default 120. Bug fix: ollama 0.6.2's Client defaults to no
            timeout at all, so a stuck/unreachable daemon blocked forever.
        client: Optional pre-built ``ollama.Client`` (used by tests to avoid
            the daemon). When provided, the ``ollama`` package is never imported
            and ``timeout`` is not applied (caller owns the client's config).
    """

    def __init__(
        self,
        *,
        model: str = "qwen2.5:7b",
        host: str | None = None,
        timeout: float | int = 120,
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
        self._client = Client(host=host, timeout=timeout) if host is not None else Client(timeout=timeout)

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
