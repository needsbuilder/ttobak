"""LLM 프로바이더 선택 — 기본은 로컬 Ollama(독립 구동), 원격 Anthropic 은 선택.

또박은 로컬 오픈웨이트 모델(Qwen2.5-7B / Kanana-1.5-8B, 모두 Apache-2.0)만으로
인터넷 없이 완결 동작한다. 원격 상용 API 는 교체 가능한 선택지 중 하나일 뿐이며,
어느 것도 파이프라인의 필수 구성요소가 아니다 — `LLMProvider` Protocol 을 만족하는
어떤 구현으로도 갈아끼울 수 있다.

앱 빌더·CLI 는 이 팩토리만 호출하고 환경 분기를 직접 하지 않는다(라이선스/CI 안전성).

구성에 실패하면 FakeProvider(결정론적 고정 응답)로 폴백하되, **반드시 stderr 에
경고를 남긴다.** 스텁 응답을 실제 변환 결과로 오인하는 것이 조용한 폴백의 진짜
위험이기 때문이다(정직성 원칙).
"""
from __future__ import annotations

import os
import sys

from ttobak.providers import AnthropicProvider, FakeProvider, OllamaProvider
from ttobak.providers.base import LLMProvider

DEFAULT_PROVIDER_ENV = "TTOBAK_PROVIDER"

#: 이름·환경변수가 모두 없을 때 고르는 프로바이더. 로컬 독립 구동이 기본이다.
DEFAULT_PROVIDER = "ollama"

# Deterministic stub output for the CI/no-key fallback (canonical FakeProvider
# raises when its queue empties with no default, so a default is required).
_FAKE_DEFAULT = "쉬운 글로 바꾼 결과입니다.\n자세한 내용은 원문을 확인하세요."

_STUB_NOTICE = (
    "[또박] 경고: '{name}' 프로바이더를 구성하지 못해 데모 스텁으로 폴백했습니다"
    "{reason}.\n"
    "[또박] 지금 나오는 변환 결과는 실제 모델 출력이 아니라 고정 응답입니다.\n"
    "[또박] 로컬 실행: `ollama serve` 후 `ollama pull qwen2.5:7b` "
    "(pip install 'ttobak[ollama]') → `ttobak web`\n"
)


def _fallback_to_stub(name: str, exc: BaseException | None = None) -> FakeProvider:
    """FakeProvider 로 폴백하면서 stderr 에 눈에 띄게 알린다."""
    reason = f" ({type(exc).__name__}: {exc})" if exc is not None else ""
    print(_STUB_NOTICE.format(name=name, reason=reason), file=sys.stderr, end="")
    return FakeProvider(default=_FAKE_DEFAULT)


def make_provider(name: str | None = None) -> LLMProvider:
    """이름으로 프로바이더를 생성한다.

    name=None 이면 $TTOBAK_PROVIDER 를 읽고, 없으면 :data:`DEFAULT_PROVIDER`
    ("ollama" — 로컬 독립 구동)를 기본으로 한다.

    구성 실패(ollama 패키지·데몬 부재, ANTHROPIC_API_KEY 부재 등) 시에는
    FakeProvider 로 폴백한다 — 데모/CI 가 라이브 API 없이도 항상 떠야 하기
    때문이다. 폴백은 언제나 stderr 경고를 동반한다.
    """
    if name is None:
        name = os.environ.get(DEFAULT_PROVIDER_ENV) or DEFAULT_PROVIDER
    name = name.strip().lower()

    if name == "fake":
        return FakeProvider(default=_FAKE_DEFAULT)

    if name == "ollama":
        try:
            return OllamaProvider()
        except Exception as exc:  # noqa: BLE001 — 어떤 구성 실패든 데모는 떠야 한다
            return _fallback_to_stub("ollama", exc)

    if name == "anthropic":
        try:
            return AnthropicProvider()
        except Exception as exc:  # noqa: BLE001 — 동상
            return _fallback_to_stub("anthropic", exc)

    return _fallback_to_stub(name)
