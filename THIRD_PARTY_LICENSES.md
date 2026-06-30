# Third-Party Licenses

Ttobak is licensed Apache-2.0. It depends on the components below.
All licenses verified against the design spec §9 (2026-06-30).
Pictogram assets are documented separately in `assets/README.md` (CC BY-SA, kept out of the Apache code tree per spec §9.4).

## Runtime (ship-path) dependencies

| Component | License | Notes |
|---|---|---|
| pydantic | MIT | data models |
| kiwipiepy (Kiwi) | LGPL-3.0 | morphological analysis; used as a *separate* dependency (no static relink, source unmodified) per spec §9.6 item 3 |
| pypdf | BSD-3-Clause | PDF text/layout |
| pdfminer.six | MIT | PDF mining (complement) |
| hwp-hwpx-parser | Apache-2.0 | HWPX (best-effort); runtime deps olefile (BSD-2) + python-docx (MIT) |
| dateparser | Apache-2.0 | date normalization (ko locale) |
| jinja2 | BSD-3-Clause | renderer templates |
| gradio | Apache-2.0 | web demo wrapper |

## Dev / CI dependencies

| Component | License | Notes |
|---|---|---|
| pytest | MIT | tests |
| pip-licenses | MIT | license allowlist gate (CI) |

## Avoided copyleft / non-commercial components (spec §9.5)

These are deliberately NOT used in any shipped artifact (repo, demo, video):

| Component | License | Why avoided | Replacement |
|---|---|---|---|
| pyhwp | AGPL-3.0 | network copyleft would infect engine+web+MCP | hwp-hwpx-parser (Apache-2.0) |
| KoNLPy (+ wrapped GPL engines) | GPL | copyleft | kiwipiepy (LGPL, separate, non-GPL) |
| Qwen2.5-3B / 72B | NC / custom | non-commercial / MAU gate | Qwen2.5-7B/14B/32B (Apache-2.0) |
| Kanana-2-30B | custom NC gate | excluded from ship path | Kanana-1.5-8B/2.1B (Apache-2.0) |
| EXAONE 3.5/4.0 | EXAONE AI Model License (NC) | non-commercial | documented as known NC alternative only; not used |
| ARASAAC / KAAC pictograms | CC BY-NC-SA / NC | non-commercial | Mulberry (CC BY-SA 2.0 UK) / OpenMoji (CC BY-SA 4.0) |
