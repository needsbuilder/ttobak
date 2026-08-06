# Third-Party Licenses

Ttobak is licensed under Apache-2.0 (see `LICENSE`). This file enumerates every
third-party component Ttobak ships, depends on, or documents, per spec §9.1–9.4.
All entries verified 2026-06-30; shipped-closure re-verified 2026-07-01;
dependency closure and source URLs re-verified 2026-08-06. Risk:
clean / caution / blocker.

## Code dependencies (spec 9.1)

> **Shipped vs documented (verified 2026-07-01).** The MVP's actual installed
> runtime closure is `pyproject.toml [project.dependencies]`: **pydantic,
> kiwipiepy, pypdf, pdfminer.six, hwp-hwpx-parser, jinja2, gradio** — plus
> optional extras **anthropic, ollama, dates, pip-licenses**. The remaining rows
> (transformers, sentence-transformers, pytesseract, opencv-python-headless,
> bert-score, kf-deberta, korean-number/es-hangul, spaCy, fastapi, uvicorn, mcp)
> are **documented / stretch components not installed or imported in the MVP** —
> retained for license transparency, not shipped. `dateparser` moved from
> `[project.dependencies]` to the `dates` extra on 2026-08-06 (issue #14): no
> module imports it, and stdlib `datetime` is the authoritative date path.
>
> **Source column = the official source repository, not the distribution page**,
> so that a reviewer can read each `LICENSE` file at its origin. Two exceptions
> are recorded honestly rather than guessed: `olefile` publishes no repository
> field on PyPI (its GitHub is reachable only through the Download URL), and
> `korean-number` publishes no project URLs at all — both are stretch/parser
> rows, and neither is imported by the MVP.

| Component | Package | License | Risk | Source |
|---|---|---|---|---|
| HWP/HWPX parser | hwp-hwpx-parser | Apache-2.0 [^hwp-lic] | clean | https://github.com/KimDaehyeon6873/hwp-hwpx-parser |
| parser runtime dep | olefile | BSD-2-Clause | clean | https://github.com/decalage2/olefile |
| parser runtime dep | python-docx | MIT | clean | https://github.com/python-openxml/python-docx |
| PDF text/layout | pypdf | BSD-3-Clause | clean | https://github.com/py-pdf/pypdf |
| PDF mining | pdfminer.six | MIT | clean | https://github.com/pdfminer/pdfminer.six |
| OCR binding (stretch) | pytesseract | Apache-2.0 | clean | https://github.com/madmaze/pytesseract |
| Image processing (stretch) | opencv-python-headless | Apache-2.0 (FFmpeg LGPL bundled, noticed) | caution | https://github.com/opencv/opencv-python |
| Morphological analyzer | kiwipiepy | LGPL-3.0 (separate dep) | caution | https://github.com/bab2min/kiwipiepy |
| Semantic similarity | bert-score | MIT | clean | https://github.com/Tiiiger/bert_score |
| Embeddings | sentence-transformers | Apache-2.0 | clean | https://github.com/huggingface/sentence-transformers |
| Transformer framework | transformers | Apache-2.0 | clean | https://github.com/huggingface/transformers |
| NLI (fidelity) | kf-deberta-base-cross-nli | MIT | clean | https://huggingface.co/deliciouscat/kf-deberta-base-cross-nli |
| Korean number normalization | korean-number / es-hangul | permissive | clean | https://pypi.org/project/korean-number/ (no project URLs published) |
| Date parsing (optional extra `dates`, not imported) | dateparser | BSD-3-Clause | clean | https://github.com/scrapinghub/dateparser |
| NER (stretch — roadmap, not shipped) | spaCy ko_core_news_lg | MIT (code) / CC BY-SA 4.0 (model asset) | clean | https://huggingface.co/spacy/ko_core_news_lg |
| Web API | fastapi | MIT | clean | https://github.com/fastapi/fastapi |
| ASGI server | uvicorn | BSD-3-Clause | clean | https://github.com/encode/uvicorn |
| Renderer templates | jinja2 | BSD-3-Clause | clean | https://github.com/pallets/jinja |
| Web demo | gradio | Apache-2.0 | clean | https://github.com/gradio-app/gradio |
| Data validation | pydantic | MIT | clean | https://github.com/pydantic/pydantic |
| MCP SDK (stretch) | mcp | MIT (pinned >=1.27,<2) | clean | https://github.com/modelcontextprotocol/python-sdk |
| Local LLM runtime | Ollama | MIT | clean | https://github.com/ollama/ollama |
| Audit tooling | pip-licenses | MIT | clean | https://github.com/raimon49/pip-licenses |

[^hwp-lic]: Verified 2026-08-06 — `hwp-hwpx-parser` publishes **no license field**
in its PyPI metadata, and GitHub's license detector reports `NOASSERTION`. The
repository's `LICENSE` file is nonetheless a verbatim Apache License 2.0
(“Copyright 2024 HWP-HWPX Parser Contributors”), which is the basis for the
Apache-2.0 entry above. Recorded because an empty metadata field is exactly the
kind of gap a license review flags, and the answer should not have to be
re-derived.

## Model weights (spec 9.2)

| Model | License | Risk | Notes |
|---|---|---|---|
| Qwen2.5 — 0.5B/1.5B/7B/14B/32B | Apache-2.0 | clean | requires "Built with Qwen" attribution |
| Kanana-1.5 — 8B / 2.1B (Kakao) | Apache-2.0 | clean | licence-clean alternative, **not** the default and not pulled by Ttobak — absent from the Ollama official library (verified 2026-07-29); the shipped local default is `qwen2.5:7b` |
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
