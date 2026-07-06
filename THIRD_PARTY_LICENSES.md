# Third-Party Licenses

Ttobak is licensed under Apache-2.0 (see `LICENSE`). This file enumerates every
third-party component Ttobak ships, depends on, or documents, per spec §9.1–9.4.
All entries verified 2026-06-30; shipped-closure re-verified 2026-07-01. Risk:
clean / caution / blocker.

## Code dependencies (spec 9.1)

> **Shipped vs documented (verified 2026-07-01).** The MVP's actual installed
> runtime closure is `pyproject.toml [project.dependencies]`: **pydantic,
> kiwipiepy, pypdf, pdfminer.six, hwp-hwpx-parser, dateparser, jinja2, gradio**
> — plus optional extras **anthropic, ollama, pip-licenses**. The remaining rows
> (transformers, sentence-transformers, pytesseract, opencv-python-headless,
> bert-score, kf-deberta, korean-number/es-hangul, spaCy, fastapi, uvicorn, mcp)
> are **documented / stretch components not installed or imported in the MVP** —
> retained for license transparency, not shipped. `dateparser` is declared but
> currently used only as a documented optional cross-check (stdlib `datetime` is
> the authoritative date path).

| Component | Package | License | Risk | Source |
|---|---|---|---|---|
| HWP/HWPX parser | hwp-hwpx-parser | Apache-2.0 | clean | https://pypi.org/project/hwp-hwpx-parser/ |
| parser runtime dep | olefile | BSD-2-Clause | clean | https://pypi.org/project/olefile/ |
| parser runtime dep | python-docx | MIT | clean | https://pypi.org/project/python-docx/ |
| PDF text/layout | pypdf | BSD-3-Clause | clean | https://pypi.org/project/pypdf/ |
| PDF mining | pdfminer.six | MIT | clean | https://pypi.org/project/pdfminer.six/ |
| OCR binding (stretch) | pytesseract | Apache-2.0 | clean | https://pypi.org/project/pytesseract/ |
| Image processing (stretch) | opencv-python-headless | Apache-2.0 (FFmpeg LGPL bundled, noticed) | caution | https://github.com/opencv/opencv-python |
| Morphological analyzer | kiwipiepy | LGPL-3.0 (separate dep) | caution | https://pypi.org/project/kiwipiepy/ |
| Semantic similarity | bert-score | MIT | clean | https://pypi.org/project/bert-score/ |
| Embeddings | sentence-transformers | Apache-2.0 | clean | https://pypi.org/project/sentence-transformers/ |
| Transformer framework | transformers | Apache-2.0 | clean | https://github.com/huggingface/transformers |
| NLI (fidelity) | kf-deberta-base-cross-nli | MIT | clean | https://huggingface.co/deliciouscat/kf-deberta-base-cross-nli |
| Korean number normalization | korean-number / es-hangul | permissive | clean | https://pypi.org/project/korean-number/ |
| Date parsing | dateparser | BSD-3-Clause | clean | https://github.com/scrapinghub/dateparser |
| NER (primary) | spaCy ko_core_news_lg | MIT (code) / CC BY-SA 4.0 (model asset) | clean | https://huggingface.co/spacy/ko_core_news_lg |
| Web API | fastapi | MIT | clean | https://github.com/fastapi/fastapi |
| ASGI server | uvicorn | BSD-3-Clause | clean | https://github.com/encode/uvicorn |
| Renderer templates | jinja2 | BSD-3-Clause | clean | https://github.com/pallets/jinja |
| Web demo | gradio | Apache-2.0 | clean | https://github.com/gradio-app/gradio |
| Data validation | pydantic | MIT | clean | https://github.com/pydantic/pydantic |
| MCP SDK (stretch) | mcp | MIT (pinned >=1.27,<2) | clean | https://github.com/modelcontextprotocol/python-sdk |
| Local LLM runtime | Ollama | MIT | clean | https://github.com/ollama/ollama |
| Audit tooling | pip-licenses | MIT | clean | https://pypi.org/project/pip-licenses/ |

## Model weights (spec 9.2)

| Model | License | Risk | Notes |
|---|---|---|---|
| Qwen2.5 — 0.5B/1.5B/7B/14B/32B | Apache-2.0 | clean | requires "Built with Qwen" attribution |
| Kanana-1.5 — 8B / 2.1B (Kakao) | Apache-2.0 | clean | recommended local fallback |
| Qwen2.5 — 3B / 72B | Qwen RESEARCH (NC) / custom | blocker | Non-Commercial — excluded, not shipped |
| Kanana-2 — 30B | Kanana License (gated) | blocker | excluded, not shipped |
| EXAONE 3.5/4.0 (LG) | EXAONE AI Model License — Non-Commercial | blocker | excluded, not shipped (documented alternative only) |

## Pictogram assets (spec 9.3 — shipped separately under /assets)

| Set | License | Risk | Source |
|---|---|---|---|
| Mulberry Symbols (primary) | CC BY-SA 2.0 UK (website) / 4.0 (bundled LICENSE, shipped verbatim) [^mulberry-lic] | caution (SA, commercial OK) | https://mulberrysymbols.org/ |
| OpenMoji (secondary) | CC BY-SA 4.0 | caution (SA, commercial OK) | https://openmoji.org/ |
| ARASAAC / KAAC | CC BY-NC-SA / NC | blocker | Non-Commercial — avoided, not shipped |

[^mulberry-lic]: Verified 2026-07-06 — mulberrysymbols.org states the requested
attribution as "CC BY-SA 2.0 UK: England & Wales", but the `LICENSE.txt` bundled
with the actual symbol files (GitHub release v3.5.2, 2025-09-17) references
CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). We ship the
bundled 4.0 file verbatim at `assets/pictograms/mulberry/LICENSE` and disclose
the discrepancy rather than silently pick one; both versions are ShareAlike and
permit commercial use, and neither infects the Apache-2.0 code (separate work,
path-reference only). Full mapping in `assets/pictograms/mulberry/ATTRIBUTION.md`.

## Avoided copyleft / non-commercial (spec 9.5)

| Component | License | Status |
|---|---|---|
| pyhwp | AGPL-3.0 | blocker — avoided (replaced by hwp-hwpx-parser) |
| KoNLPy (+ wrapped GPL engines) | GPL | blocker — avoided (replaced by kiwipiepy) |
| EXAONE | EXAONE NC license | blocker — excluded, not shipped |
| ARASAAC / KAAC pictograms | CC BY-NC-SA / NC | blocker — avoided, not shipped |

## License decisions (spec 9.4)

- Code = Apache-2.0 (Python core, web, MCP).
- Dataset = CC BY 4.0.
- Pictograms = each set's CC BY-SA, kept under `/assets`, referenced by
  path/URL only and never embedded inline/base64 into Apache code or the
  CC BY dataset (ShareAlike-contamination avoidance).
