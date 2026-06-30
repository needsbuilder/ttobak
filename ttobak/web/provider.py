"""LLM 프로바이더 선택 — 기본 Anthropic, 키 없으면 FakeProvider로 우아하게 폴백.

앱 빌더·CLI는 이 팩토리만 호출하고 환경 분기를 직접 하지 않는다(라이선스/CI 안전성).
"""
from __future__ import annotations

import os

from ttobak.providers import AnthropicProvider, FakeProvider
from ttobak.providers.base import LLMProvider

DEFAULT_PROVIDER_ENV = "TTOBAK_PROVIDER"

# Deterministic stub output for the CI/no-key fallback (canonical FakeProvider
# raises when its queue empties with no default, so a default is required).
_FAKE_DEFAULT = "쉬운 글로 바꾼 결과입니다.\n자세한 내용은 원문을 확인하세요."


def make_provider(name: str | None = None) -> LLMProvider:
    """이름으로 프로바이더를 생성한다.

    name=None 이면 $TTOBAK_PROVIDER 를 읽고, 없으면 "anthropic" 을 기본으로 한다.
    "anthropic" 구성 실패(예: ANTHROPIC_API_KEY 부재) 시 FakeProvider 로 폴백한다 —
    데모/CI가 라이브 API 없이도 항상 동작해야 하기 때문이다.
    """
    if name is None:
        name = os.environ.get(DEFAULT_PROVIDER_ENV) or "anthropic"
    name = name.strip().lower()

    if name == "fake":
        return FakeProvider(default=_FAKE_DEFAULT)

    if name == "anthropic":
        try:
            return AnthropicProvider()
        except Exception:
            return FakeProvider(default=_FAKE_DEFAULT)

    return FakeProvider(default=_FAKE_DEFAULT)
