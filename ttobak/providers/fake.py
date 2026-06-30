"""Deterministic provider for tests.

FakeProvider returns a scripted queue of responses (FIFO) and records every
call. It implements the LLMProvider Protocol structurally. Tests across ALL
modules use this — never a live LLM API.
"""

from __future__ import annotations


class FakeProvider:
    """A scripted, deterministic LLMProvider implementation.

    Args:
        responses: Responses returned in FIFO order, one per ``generate`` call.
        default: Returned once the scripted queue is exhausted. If ``None`` and
            the queue is empty, ``generate`` raises ``IndexError``.
    """

    def __init__(
        self,
        responses: list[str] | None = None,
        *,
        default: str | None = None,
    ) -> None:
        self._queue: list[str] = list(responses) if responses is not None else []
        self._default = default
        self.calls: list[dict] = []

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        self.calls.append(
            {"prompt": prompt, "system": system, "max_tokens": max_tokens}
        )
        if self._queue:
            return self._queue.pop(0)
        if self._default is not None:
            return self._default
        raise IndexError(
            "FakeProvider response queue is empty and no default was set"
        )
