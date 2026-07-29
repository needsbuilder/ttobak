# LLM Providers

Ttobak is provider-agnostic. Every provider implements the
`ttobak.providers.base.LLMProvider` Protocol:

```python
def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str: ...
```

Select one with the factory:

```python
from ttobak.providers import get_provider

provider = get_provider("ollama")             # default — local, open-weight
provider = get_provider("anthropic")          # optional remote alternative
provider = get_provider("fake", responses=[]) # tests only
```

**Ttobak runs end to end with no network and no commercial API.** The only
model it needs is an open-weight one you download and serve yourself. Every
remote option is an interchangeable alternative behind the same Protocol, never
a required component — nothing in the pipeline breaks if you never configure
one.

## Providers

| Name        | Class               | Use                                          | Dependency          |
|-------------|---------------------|----------------------------------------------|---------------------|
| `ollama`    | `OllamaProvider`    | **Default**; local, model `qwen2.5:7b`       | `ttobak[ollama]`    |
| `anthropic` | `AnthropicProvider` | Optional remote; model `claude-opus-4-8`     | `ttobak[anthropic]` |
| `fake`      | `FakeProvider`      | Deterministic tests (never a live API)       | none                |

`ttobak web` with no `--provider` reads `$TTOBAK_PROVIDER`, then falls back to
`ollama`. If a provider cannot be constructed (package missing, daemon down, no
API key), the demo stays up on `FakeProvider` — but it says so loudly, on stderr
**and** as a banner in the web UI. A stub response must never be mistaken for a
real conversion.

## Local model decision (Apache-2.0 only, license gate)

- **Default: Qwen2.5-7B** (Alibaba, Apache-2.0) — `ollama pull qwen2.5:7b`.
  Chosen as the default because it is in Ollama's official library, so a
  first-time run needs no extra setup. `get_provider("ollama")` uses
  `model="qwen2.5:7b"`. Also fine: `qwen2.5:14b`.
- **Alternative: Kanana-1.5** (Kakao, Apache-2.0) — strong Korean, but **not**
  in Ollama's official library (`ollama.com/library/kanana` → 404, checked
  2026-07-29). It needs a Hugging Face GGUF tag, e.g.
  `get_provider("ollama", model="hf.co/<repo>-GGUF:<quant>")`. It was the
  default until 2026-07-29; a bare `kanana-1.5-8b` tag is unpullable, so the
  default path failed on `ollama pull`.
- **Excluded from the shipped path (NC / gated):** Qwen2.5-3B/72B,
  Kanana-2-30B, EXAONE. Documented as known NC alternatives only.

Real providers import their SDK lazily at construction, so the package imports
cleanly without the optional extras and the test suite (FakeProvider only) needs
no LLM dependency.
