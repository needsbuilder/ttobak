# LLM Providers

Ttobak is provider-agnostic. Every provider implements the
`ttobak.providers.base.LLMProvider` Protocol:

```python
def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str: ...
```

Select one with the factory:

```python
from ttobak.providers import get_provider

provider = get_provider("anthropic")          # demo default (Claude)
provider = get_provider("ollama")             # local fallback
provider = get_provider("fake", responses=[]) # tests only
```

## Providers

| Name        | Class               | Use                                   | Dependency           |
|-------------|---------------------|---------------------------------------|----------------------|
| `fake`      | `FakeProvider`      | Deterministic tests (never a live API) | none                 |
| `anthropic` | `AnthropicProvider` | Demo default; model `claude-opus-4-8` | `ttobak[anthropic]`  |
| `ollama`    | `OllamaProvider`    | Local; default `kanana-1.5-8b`        | `ttobak[ollama]`     |

## Local model decision (Apache-2.0 only, license gate)

- **1st choice (default): Kanana-1.5-8B** (Kakao, Apache-2.0) — strong Korean.
  `get_provider("ollama")` uses `model="kanana-1.5-8b"`.
- **2nd choice: Qwen2.5-7B / 14B** (Apache-2.0) —
  `get_provider("ollama", model="qwen2.5:7b")`.
- **Excluded from the shipped path (NC / gated):** Qwen2.5-3B/72B,
  Kanana-2-30B, EXAONE. Documented as known NC alternatives only.

Demo runs default to the Anthropic API for quality; the local Ollama path is a
documented, license-clean fallback. Real providers import their SDK lazily at
construction, so the package imports cleanly without the optional extras and
the test suite (FakeProvider only) needs no LLM dependency.
