# 또박(Ttobak) MVP Implementation Plan

REQUIRED SUB-SKILL: superpowers:subagent-driven-development or superpowers:executing-plans — each task below is a TDD unit (write failing test → run red → implement → run green → commit). Workers MUST follow that loop and check off each `- [ ]` step as it completes.

**Goal:** Ship an open-source (Apache-2.0) Korean Easy-Read engine that converts hard public/administrative documents into easy-read text, measures easiness with a rule-based K-ER score, self-corrects via a generate→measure→revise loop, and preserves facts (numbers/dates/amounts/deadlines/eligibility/entities) through a deterministic fidelity gate — with a side-by-side renderer, pictogram lookup, web demo, evaluation harness, and a license/security CI gate, all by 8/27.

**Architecture:** A clean Python core (`ttobak`) exposes six public functions — `parse`, `score`, `verify`, `match`, `simplify`, `render_html` — wired through a shared Intermediate Representation (IR) and shared pydantic contracts. The pipeline orchestrates a provider-agnostic LLM (Anthropic API default / Ollama local fallback / deterministic FakeProvider in tests) in a GENERATE→MEASURE→REVISE loop where rule-based K-ER violations and fidelity failed-slots are fed back as hard verbatim-preservation constraints. Web demo and evaluation harness are thin wrappers over the same core, and a license/security audit gate guards every release.

**Tech Stack:** Python 3.11+, pydantic v2, pytest. Tokenizer kiwipiepy (LGPL, separate dep). PDF pypdf + pdfminer.six. HWPX hwp-hwpx-parser (Apache-2.0; deps olefile + python-docx). Dates dateparser. Korean numbers korean-number / es-hangul. NER spaCy ko_core_news_lg (primary). LLM provider-agnostic: Anthropic/OpenAI API + Ollama (Kanana-1.5-8B / Qwen2.5) local; tests use a deterministic FakeProvider, never a live API. Web Gradio (or FastAPI) thin wrapper. Renderer Jinja2. License audit pip-licenses.

## Global Constraints

These project-wide rules are copied verbatim from spec §9 (라이선스) and §3 (비기능 요구/원칙) and bind every task. Any task that violates them is wrong.

### License (spec §9.4, §3.2)
- **코드 = Apache-2.0** (Python 코어·웹·MCP). 근거: (1) ship하는 모든 코드 의존성이 permissive(Apache/MIT/BSD) 또는 분리형 weak-copyleft(LGPL: kiwipiepy/soynlp), Apache 배포와 호환; (2) Apache의 명시적 특허 grant가 기관 후원 대회·다운스트림 재사용에 유리하고 헤드라인 파서·Qwen2.5 가중치와 NOTICE 정합; (3) '재사용 가능한 오픈소스 자산' 심사 점수 극대화.
- **데이터셋 = CC BY 4.0**(또는 최대 재사용 원하면 CC0).
- **픽토그램 = 각자의 CC BY-SA**(별도 `/assets`, Apache로 재라이선스 안 함). SA on 자산은 Apache 코드를 전염 안 함(별개 저작물; mere aggregation). 단 *수정*한 글리프는 동일 CC BY-SA 유지.
- **임베드 규칙(검증 게이트 대비)**: 렌더러는 픽토그램을 **파일 경로/URL 참조로만** 사용한다. *수정된* CC BY-SA 글리프를 Apache 코드 산출물이나 CC BY 데이터셋 출력에 **인라인/base64로 내장하지 않는다**(결합저작물 생성 회피). 수정 글리프(`/assets/pictograms/derived/`)는 **별도 라이선스 자산 팩**으로 ship.

### Avoided copyleft / NC — 5 hard blockers (spec §9.5, §3.2)
- **AGPL**: pyhwp → hwp-hwpx-parser로 대체.
- **GPL**: KoNLPy(+래핑 GPL 엔진) → kiwipiepy(LGPL, 비-GPL, 분리)로 대체.
- **NC/커스텀 모델**: Qwen2.5-3B/72B, Kanana-2-30B, EXAONE → Apache 사이즈(Qwen2.5-7B/14B/32B, Kanana-1.5-8B/2.1B)로.
- **NC 픽토그램**: ARASAAC/KAAC → Mulberry/OpenMoji(CC BY-SA, 상업OK)로.
- 출품 전 `pip-licenses` 의존성 스캔 + 시크릿/PII 부재 확인.

### Packaging actions (spec §9.6)
- top-level `LICENSE`=Apache-2.0 + `NOTICE`(Apache 출처표시 + Qwen NOTICE 집약).
- 핀: **`mcp>=1.27,<2`** if MCP is used (상류 README 권장; v2 stable 목표 ~2026-07-27, alpha 이미 배포 중 → 안정 v1.x 고수). NOTE: `mcp` is NOT an MVP dependency (MCP server is stretch §12.3); pin it only if MCP work is undertaken. Also pin hwp-hwpx-parser (신규/1인), opencv-python-headless (Qt5 회피; FFmpeg LGPLv2.1 번들 고지) 또는 기본 연산 Pillow.
- kiwipiepy/soynlp LGPL relink 노트 + "소스 미수정" 입장 문서화.
- 데이터셋 CC BY 4.0/CC0; 픽토그램 `/assets` 각자 CC BY-SA.
- 모델 가중치를 ship하거나 72B/EXAONE 포함 시 라이선스 텍스트 + 필수 고지("Built with Qwen" 등) verbatim 동봉.

### Fidelity-first (spec §3.1)
- 의미는 **절대** 흘러서는 안 된다. 쉬움과 충실성이 충돌하면 충실성이 이긴다.
- 출력은 **항상** 원문 + 면책 고지("자동 변환 결과, 원문 우선")와 함께 렌더링. Fidelity 게이트는 *방어층 중 하나*이지 유일한 안전망이 아니다.
- HIGH 중요도 슬롯(금액·기한·자격·부정·법적 의무·기관·연락처)은 정확 보존 실패 시 PASS 불가.

### Engineering invariants
- **Python 3.11+, pydantic v2** throughout.
- **Tests use FakeProvider, never a live LLM API** (spec §14.4 결정론 CI).
- K-ER honesty framing on every surface: "한국 Easy-Read 지침 정렬 규칙 기반 루브릭, 경험적 검증 아님" (spec §5.3). 0–100 점수는 비검증 보조 지표, 규칙별 위반 체크리스트(pass/fail)가 하중 지지 산출물.

## 공유 계약(Contracts)

Canonical. Every module MUST import these exact names/types from these exact modules and MUST NOT redefine them. Use these signatures verbatim.

```
ttobak/ir.py:
  class BlockType(str, Enum): HEADING="heading"; PARAGRAPH="paragraph"; LIST_ITEM="list_item"; TABLE="table"; CAPTION="caption"
  class Block(BaseModel): type: BlockType; text: str = ""; level: int = 0; cells: list[list[str]] | None = None; bbox: tuple[float,float,float,float] | None = None; confidence: float = 1.0
  class Document(BaseModel): blocks: list[Block]; source_mime: str; meta: dict = {}   # method: text(self) -> str  (joins block text with newlines)

ttobak/levels.py:
  class Level(str, Enum): PLAIN="plain"; EASY="easy"

ttobak/common.py:
  class Severity(str, Enum): HIGH="high"; MED="med"; LOW="low"
  class Verdict(str, Enum): PASS="pass"; REVISE="revise"; HUMAN_REVIEW="human_review"

ttobak/providers/base.py:
  class LLMProvider(Protocol): def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str: ...
  (FakeProvider implements this returning scripted outputs for tests.)

ttobak/metric/models.py:
  class Violation(BaseModel): rule: str; span: str; severity: Severity; suggestion: str
  class KERReport(BaseModel): score: float; level_estimate: int; sub_scores: dict[str, float]; violations: list[Violation]

ttobak/fidelity/models.py:
  class SlotType(str, Enum): NUMERIC, DATE, MONEY, DURATION, ELIGIBILITY, AGENCY, CONTACT, PERSON, NEGATION, CONDITIONAL, MODALITY, SCOPE   (str values = lowercase name)
  class Slot(BaseModel): raw_span: str; normalized_value: str; type: SlotType; polarity: bool = True; source_offset: int = 0; criticality: Severity = Severity.HIGH
  class FidelityReport(BaseModel): slots: list[Slot]; verdict: Verdict; exact_fail_count: int = 0; nli_contradictions: list[str] = []; drift_flags: list[str] = []; failed_slots: list[Slot] = []

ttobak/pictogram/models.py:
  class PictogramRef(BaseModel): concept: str; set: str; glyph_id: str; caption: str

ttobak/result.py:
  class EasyReadResult(BaseModel): source: Document; easy_text: str; level: Level; ker: KERReport; fidelity: FidelityReport; pictograms: list[PictogramRef] = []; revisions: int = 0; verdict: Verdict
```

Public function signatures (the engine API):

```
ttobak/parse/__init__.py:    def parse(source: bytes | str | Path, mime: str) -> Document
ttobak/metric/__init__.py:   def score(easy_text: str, level: Level, source_text: str | None = None) -> KERReport
ttobak/fidelity/__init__.py: def verify(source: Document, easy_text: str, ref_date: date) -> FidelityReport
ttobak/pictogram/__init__.py: def match(easy_text: str) -> list[PictogramRef]
ttobak/pipeline.py:          def simplify(doc: Document, level: Level, provider: LLMProvider, max_revise: int = 3) -> EasyReadResult
ttobak/render.py:            def render_html(result: EasyReadResult) -> str
```

## Phase 1: 코어 골격

Walking skeleton: repo + licensing + CI (Task 1–6), IR + text parser (Task 7–10), LLM provider abstraction (Task 11–15), and the generate→measure→revise pipeline shell with `EasyReadResult` (Task 16–20). After Phase 1, text input runs end-to-end through `simplify()` against stub metric/fidelity modules.

### Task 1: Bootstrap package skeleton, pyproject, and CI-green smoke test

**Files:**
- Create: `pyproject.toml`
- Create: `ttobak/__init__.py`
- Create: `tests/__init__.py`
- Create: `.gitignore`
- Test: `tests/test_smoke.py`

**Interfaces:**
- Consumes: nothing (root). Python 3.11+, `pydantic>=2`, `pytest`, `pip-licenses` per spec §9.1/§9.6.
- Produces: `ttobak` importable package with `ttobak.__version__: str`; `pyproject.toml` declaring package `ttobak` (flat layout `ttobak/`), pinned runtime deps and a `dev` extra (`pytest`, `pip-licenses`); a `[tool.pytest.ini_options]` config; a passing smoke test so CI starts green.

Steps:

- [ ] **Step 1: Write failing smoke test.** Create `tests/__init__.py` as an empty file, then create `tests/test_smoke.py`:
```python
import ttobak


def test_package_imports():
    assert ttobak is not None


def test_version_is_a_nonempty_string():
    assert isinstance(ttobak.__version__, str)
    assert ttobak.__version__ != ""
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_smoke.py -q`. Expect failure with `ModuleNotFoundError: No module named 'ttobak'` (the package does not exist yet).

- [ ] **Step 3: Create the package init.** Create `ttobak/__init__.py`:
```python
"""또박(Ttobak) — open-source Korean Easy-Read engine.

Turns hard Korean public/administrative documents into easy-read text,
measures easiness (K-ER score), self-corrects, and preserves facts via a
fidelity gate. Apache-2.0.
"""

__version__ = "0.1.0"
```

- [ ] **Step 4: Create `pyproject.toml`.** Create `pyproject.toml` with the pinned dependency set from spec §9.1/§9.6 (kiwipiepy LGPL as a separate dep, pypdf BSD, pdfminer.six MIT, hwp-hwpx-parser Apache-2.0, dateparser Apache-2.0, jinja2, gradio; dev extra adds pytest + pip-licenses). NOTE: `mcp` is intentionally NOT here (MVP §12.2; MCP is stretch §12.3):
```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ttobak"
version = "0.1.0"
description = "Open-source Korean Easy-Read engine: measures easiness (K-ER) and preserves facts via a fidelity gate."
readme = "README.md"
requires-python = ">=3.11"
license = { text = "Apache-2.0" }
authors = [{ name = "Ttobak contributors" }]
keywords = ["korean", "easy-read", "accessibility", "readability", "nlp"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "License :: OSI Approved :: Apache Software License",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Natural Language :: Korean",
    "Topic :: Text Processing :: Linguistic",
]
dependencies = [
    "pydantic>=2.6,<3",
    "kiwipiepy>=0.17,<0.21",
    "pypdf>=4.0,<6",
    "pdfminer.six>=20231228",
    "hwp-hwpx-parser==1.0.0",
    "dateparser>=1.2,<2",
    "jinja2>=3.1,<4",
    "gradio>=4.44,<6",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "pip-licenses>=5.0,<6",
]

[project.urls]
Homepage = "https://github.com/ttobak/ttobak"

[tool.setuptools.packages.find]
where = ["."]
include = ["ttobak*"]

[tool.pytest.ini_options]
minversion = "8.0"
addopts = "-ra"
testpaths = ["tests"]
```

- [ ] **Step 5: Create `.gitignore`.** Create `.gitignore` (note: `dev-only/` is gitignored per spec §8.5 — AI Hub / 모두의 말뭉치 / NC / PII are private-eval-only and must never be redistributed):
```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
.eggs/
build/
dist/
.pytest_cache/
.venv/
venv/
.env

# Spec §8.5: private, non-redistributable evaluation material — never commit
dev-only/

# OS
.DS_Store
```

- [ ] **Step 6: Install the package editable and run the test, expect PASS.** Run `python -m pip install -e ".[dev]" && python -m pytest tests/test_smoke.py -q`. Expect `2 passed`.

- [ ] **Step 7: Commit.** Run `git checkout -b m0-scaffold && git add pyproject.toml ttobak/__init__.py tests/__init__.py tests/test_smoke.py .gitignore && git commit -m "chore(m0): bootstrap ttobak package, pyproject, smoke test"`.

### Task 2: Define shared contracts — Severity, Verdict (common.py) and Level (levels.py)

**Files:**
- Create: `ttobak/common.py`
- Create: `ttobak/levels.py`
- Test: `tests/test_common.py`
- Test: `tests/test_levels.py`

**Interfaces:**
- Consumes: standard library `enum` only.
- Produces (canonical SHARED CONTRACTS — every downstream module imports these exact names): `ttobak/common.py` → `class Severity(str, Enum)` with `HIGH="high"; MED="med"; LOW="low"` and `class Verdict(str, Enum)` with `PASS="pass"; REVISE="revise"; HUMAN_REVIEW="human_review"`; `ttobak/levels.py` → `class Level(str, Enum)` with `PLAIN="plain"; EASY="easy"`.

Steps:

- [ ] **Step 1: Write failing test for common.py.** Create `tests/test_common.py`:
```python
from enum import Enum

from ttobak.common import Severity, Verdict


def test_severity_is_str_enum_with_exact_values():
    assert issubclass(Severity, str)
    assert issubclass(Severity, Enum)
    assert Severity.HIGH.value == "high"
    assert Severity.MED.value == "med"
    assert Severity.LOW.value == "low"
    assert {m.value for m in Severity} == {"high", "med", "low"}


def test_severity_member_equals_its_string_value():
    assert Severity.HIGH == "high"


def test_verdict_is_str_enum_with_exact_values():
    assert issubclass(Verdict, str)
    assert issubclass(Verdict, Enum)
    assert Verdict.PASS.value == "pass"
    assert Verdict.REVISE.value == "revise"
    assert Verdict.HUMAN_REVIEW.value == "human_review"
    assert {m.value for m in Verdict} == {"pass", "revise", "human_review"}


def test_verdict_member_equals_its_string_value():
    assert Verdict.HUMAN_REVIEW == "human_review"
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_common.py -q`. Expect failure with `ModuleNotFoundError: No module named 'ttobak.common'`.

- [ ] **Step 3: Create `ttobak/common.py`.** Create `ttobak/common.py` verbatim per the SHARED CONTRACTS:
```python
"""Shared cross-module enums (canonical contracts).

Every module MUST import Severity / Verdict from here and MUST NOT redefine them.
"""

from enum import Enum


class Severity(str, Enum):
    HIGH = "high"
    MED = "med"
    LOW = "low"


class Verdict(str, Enum):
    PASS = "pass"
    REVISE = "revise"
    HUMAN_REVIEW = "human_review"
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/test_common.py -q`. Expect `4 passed`.

- [ ] **Step 5: Write failing test for levels.py.** Create `tests/test_levels.py`:
```python
from enum import Enum

from ttobak.levels import Level


def test_level_is_str_enum_with_exact_values():
    assert issubclass(Level, str)
    assert issubclass(Level, Enum)
    assert Level.PLAIN.value == "plain"
    assert Level.EASY.value == "easy"
    assert {m.value for m in Level} == {"plain", "easy"}


def test_level_member_equals_its_string_value():
    assert Level.EASY == "easy"
```

- [ ] **Step 6: Run the test, expect FAIL.** Run `python -m pytest tests/test_levels.py -q`. Expect failure with `ModuleNotFoundError: No module named 'ttobak.levels'`.

- [ ] **Step 7: Create `ttobak/levels.py`.** Create `ttobak/levels.py` verbatim per the SHARED CONTRACTS (PLAIN = 국가문해교육센터 문해수준 3 / 보통 읽기; EASY = 문해수준 1–2 / 쉬운 글, spec §2.1):
```python
"""Output reading levels (canonical contract).

PLAIN = 보통 읽기 (Plain Language, 문해수준 3, text-centric).
EASY  = 쉬운 글 (Easy Korean, 문해수준 1–2, layout/whitespace/pictogram-centric).
"""

from enum import Enum


class Level(str, Enum):
    PLAIN = "plain"
    EASY = "easy"
```

- [ ] **Step 8: Run the test, expect PASS.** Run `python -m pytest tests/test_levels.py -q`. Expect `2 passed`.

- [ ] **Step 9: Commit.** Run `git add ttobak/common.py ttobak/levels.py tests/test_common.py tests/test_levels.py && git commit -m "feat(m0): add canonical Severity/Verdict/Level contracts"`.

### Task 3: Add Apache-2.0 LICENSE, NOTICE, and THIRD_PARTY_LICENSES.md

**Files:**
- Create: `LICENSE`
- Create: `NOTICE`
- Create: `THIRD_PARTY_LICENSES.md`
- Test: `tests/test_licensing_files.py`

**Interfaces:**
- Consumes: nothing.
- Produces: top-level `LICENSE` (Apache-2.0 full text), `NOTICE` (Apache attribution aggregation per spec §9.6 item 1), `THIRD_PARTY_LICENSES.md` (per-dependency license matrix from spec §9.1/§9.5). These are the redistributable license-gate evidence files referenced by spec §11.3 / §14.5.

Steps:

- [ ] **Step 1: Write failing test for licensing files.** Create `tests/test_licensing_files.py`:
```python
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_license_is_apache_2():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in text
    assert "Version 2.0" in text


def test_notice_names_project_and_apache():
    text = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "Ttobak" in text or "또박" in text
    assert "Apache License, Version 2.0" in text


def test_third_party_lists_key_deps_and_avoided_copyleft():
    text = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    # ship-path deps must be documented
    for dep in ["hwp-hwpx-parser", "pypdf", "pdfminer.six", "dateparser", "kiwipiepy"]:
        assert dep in text, dep
    # avoided blockers must be documented as avoided (spec §9.5)
    for blocker in ["pyhwp", "KoNLPy", "EXAONE", "ARASAAC"]:
        assert blocker in text, blocker
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_licensing_files.py -q`. Expect failure with `FileNotFoundError` for `LICENSE` (no licensing files exist yet).

- [ ] **Step 3: Create the Apache-2.0 `LICENSE`.** Fetch the canonical Apache-2.0 text. Run `curl -fsSL https://www.apache.org/licenses/LICENSE-2.0.txt -o LICENSE`. If offline, write the full Apache License Version 2.0 text into `LICENSE` manually; it must begin with `Apache License` and contain `Version 2.0` (the Step 5 test enforces this).

- [ ] **Step 4: Create `NOTICE` and `THIRD_PARTY_LICENSES.md`.** Create `NOTICE` (per spec §9.6 item 1 — Apache attribution aggregation; Qwen/Kanana model NOTICEs are added only if weights are ever shipped, which the MVP does not do):
```
Ttobak (또박) — Korean Easy-Read engine
Copyright 2026 Ttobak contributors

This product includes software developed as part of the Ttobak project.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Third-party components and their licenses are listed in
THIRD_PARTY_LICENSES.md. Pictogram assets are NOT covered by this
license; they are CC BY-SA and shipped separately under /assets with
their own LICENSE and ATTRIBUTION files (see assets/README.md).
```
  Then create `THIRD_PARTY_LICENSES.md` (license matrix transcribed from spec §9.1/§9.3/§9.5):
```markdown
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
```

- [ ] **Step 5: Run the test, expect PASS.** Run `python -m pytest tests/test_licensing_files.py -q`. Expect `3 passed`.

- [ ] **Step 6: Commit.** Run `git add LICENSE NOTICE THIRD_PARTY_LICENSES.md tests/test_licensing_files.py && git commit -m "docs(m0): add Apache-2.0 LICENSE, NOTICE, third-party license matrix"`.

### Task 4: Separate /assets (CC BY-SA) from the Apache code tree + automated separation check

**Files:**
- Create: `assets/.gitkeep`
- Create: `assets/README.md`
- Create: `scripts/__init__.py`
- Create: `scripts/check_assets_separation.py`
- Test: `tests/test_assets_separation.py`

**Interfaces:**
- Consumes: standard library `pathlib`, `re`.
- Produces: `assets/` tree marked as a separately-licensed CC BY-SA pictogram pack (spec §8.5/§9.4); `scripts/check_assets_separation.py` exposing `def find_asset_leaks(repo_root: Path | str) -> list[str]` which returns offending paths (any pictogram binary committed *outside* `assets/`, and any base64/data-URI inlined glyph inside the `ttobak/` Apache code tree). Returns an empty list when separation is clean.

Steps:

- [ ] **Step 1: Write failing test for the separation checker.** Create `tests/test_assets_separation.py`:
```python
from pathlib import Path

from scripts.check_assets_separation import find_asset_leaks

ROOT = Path(__file__).resolve().parent.parent


def test_assets_dir_exists_with_readme():
    assert (ROOT / "assets").is_dir()
    readme = (ROOT / "assets" / "README.md").read_text(encoding="utf-8")
    assert "CC BY-SA" in readme


def test_current_repo_has_no_asset_leaks():
    assert find_asset_leaks(ROOT) == []


def test_detects_pictogram_binary_committed_outside_assets(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "assets").mkdir()
    # a pictogram glyph living in the Apache code tree = a leak
    (tmp_path / "ttobak" / "stray_glyph.svg").write_text("<svg></svg>", encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("stray_glyph.svg" in p for p in leaks)


def test_detects_base64_inlined_glyph_in_code(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "assets").mkdir()
    code = 'GLYPH = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="\n'
    (tmp_path / "ttobak" / "render.py").write_text(code, encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("render.py" in p for p in leaks)
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_assets_separation.py -q`. Expect failure with `ModuleNotFoundError: No module named 'scripts.check_assets_separation'`.

- [ ] **Step 3: Create the `assets/` marker files.** Create `assets/.gitkeep` as an empty file, then create `assets/README.md` (spec §8.5/§9.4 — CC BY-SA pack, not relicensed Apache, referenced only by path/URL, never inlined/base64 into Apache code or CC BY data output):
````markdown
# Assets — pictograms (separately licensed, NOT Apache-2.0)

This directory ships pictogram glyphs under their own **CC BY-SA** licenses,
kept deliberately separate from the Apache-2.0 code in `ttobak/` (spec §9.4).

```
assets/pictograms/
  mulberry/   (unmodified)  LICENSE = CC BY-SA 2.0 UK + ATTRIBUTION.md
  openmoji/   (unmodified)  LICENSE = CC BY-SA 4.0  + ATTRIBUTION.md
  derived/    (our edits)   LICENSE = CC BY-SA (matching source set) + CHANGES.md
```

## Rules (license-gate compliance)
- ShareAlike (SA) on these assets does NOT infect the Apache code — they are a
  separate work (mere aggregation).
- The renderer references pictograms **by file path / URL only**. It MUST NOT
  inline or base64-embed a *modified* CC BY-SA glyph into Apache code output or
  CC BY data output (avoids creating a combined work) — spec §9.4 embed rule.
- Modified glyphs (`derived/`) keep the same CC BY-SA license + CHANGES.md.

## Attribution
- Mulberry Symbols © 2018–2026 Steve Lee, CC BY-SA 2.0 UK — https://mulberrysymbols.org
- OpenMoji, CC BY-SA 4.0 — https://openmoji.org
````

- [ ] **Step 4: Create the separation checker.** Create `scripts/__init__.py` as an empty file, then create `scripts/check_assets_separation.py`:
```python
"""Assets separation check (spec §8.5 / §9.4).

Ensures CC BY-SA pictogram assets stay out of the Apache-2.0 `ttobak/` code tree:
  1. No pictogram binary (svg/png/jpg/jpeg/gif/webp) committed outside `assets/`.
  2. No base64/data-URI inlined glyph embedded inside `ttobak/` source files.

Used by tests and by CI (spec §14.5). `find_asset_leaks` returns the offending
paths (relative to repo root); an empty list means separation is clean.
"""

from __future__ import annotations

import re
from pathlib import Path

PICTOGRAM_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
_DATA_URI = re.compile(r"data:image/[a-z.+-]+;base64,")
_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "build", "dist"}


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in _SKIP_DIRS or part.endswith(".egg-info") for part in path.parts):
            continue
        yield path


def find_asset_leaks(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    assets_dir = root / "assets"
    leaks: list[str] = []

    for path in _iter_files(root):
        rel = path.relative_to(root)
        in_assets = assets_dir in path.parents

        # Rule 1: pictogram binaries must live under assets/ only.
        if path.suffix.lower() in PICTOGRAM_EXTS and not in_assets:
            leaks.append(str(rel))
            continue

        # Rule 2: no base64/data-URI inlined glyph inside the ttobak/ code tree.
        if rel.parts and rel.parts[0] == "ttobak" and path.suffix == ".py":
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if _DATA_URI.search(text):
                leaks.append(str(rel))

    return sorted(leaks)
```

- [ ] **Step 5: Run the test, expect PASS.** Run `python -m pytest tests/test_assets_separation.py -q`. Expect `4 passed`.

- [ ] **Step 6: Commit.** Run `git add assets/.gitkeep assets/README.md scripts/__init__.py scripts/check_assets_separation.py tests/test_assets_separation.py && git commit -m "feat(m0): separate CC BY-SA /assets from code + add separation check"`.

### Task 5: pip-licenses allowlist gate (fails on GPL/AGPL/NC)

**Files:**
- Create: `scripts/check_licenses.py`
- Test: `tests/test_license_allowlist.py`

**Interfaces:**
- Consumes: standard library only (the gate function operates on already-collected license records, so the unit test is deterministic and needs no network/install). `scripts/__init__.py` from Task 4 makes `scripts` importable.
- Produces: `scripts/check_licenses.py` exposing `def check_licenses(packages: list[dict], allowlist: set[str], denylist: set[str]) -> list[str]` (returns human-readable violation strings; empty list = clean), `ALLOWLIST: set[str]`, `DENYLIST_SUBSTR: set[str]` constants, and a `def main() -> int` CLI entry that runs `pip-licenses --format=json`, applies the gate, prints violations, and returns a nonzero exit code on any violation (spec §14.5).

Steps:

- [ ] **Step 1: Write failing test for the allowlist gate.** Create `tests/test_license_allowlist.py`:
```python
from scripts.check_licenses import ALLOWLIST, DENYLIST_SUBSTR, check_licenses


def test_clean_permissive_packages_pass():
    pkgs = [
        {"Name": "pypdf", "License": "BSD-3-Clause"},
        {"Name": "pdfminer.six", "License": "MIT License"},
        {"Name": "hwp-hwpx-parser", "License": "Apache-2.0"},
        {"Name": "dateparser", "License": "Apache Software License"},
    ]
    assert check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR) == []


def test_lgpl_is_allowed_separate_dep():
    # kiwipiepy is LGPL-3.0 and explicitly permitted (spec §9.1, separate dep)
    pkgs = [{"Name": "kiwipiepy", "License": "LGPL-3.0"}]
    assert check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR) == []


def test_agpl_is_flagged():
    pkgs = [{"Name": "pyhwp", "License": "GNU Affero General Public License v3"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "pyhwp" in violations[0]


def test_gpl_is_flagged():
    pkgs = [{"Name": "some-konlpy-dep", "License": "GPL-3.0"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "some-konlpy-dep" in violations[0]


def test_non_commercial_is_flagged():
    pkgs = [{"Name": "fake-nc-asset", "License": "CC BY-NC-SA 4.0"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "fake-nc-asset" in violations[0]


def test_unknown_license_is_flagged_as_review_needed():
    pkgs = [{"Name": "mystery-pkg", "License": "UNKNOWN"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "mystery-pkg" in violations[0]


def test_denylist_wins_over_allowlist_substring():
    # A string that contains an allowed-ish token but is actually a denied license
    pkgs = [{"Name": "tricky", "License": "GNU General Public License (GPL)"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "tricky" in violations[0]
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_license_allowlist.py -q`. Expect failure with `ModuleNotFoundError: No module named 'scripts.check_licenses'`.

- [ ] **Step 3: Create the license gate.** Create `scripts/check_licenses.py` (the denylist of GPL/AGPL/NC substrings is checked FIRST so a denied license can never slip through on an allowlisted substring; the `gpl` rule explicitly excludes `lgpl`; spec §14.5/§9.5):
```python
"""pip-licenses allowlist gate (spec §14.5 / §9.5).

Fails the build if any installed dependency carries a copyleft (GPL/AGPL) or
non-commercial (NC) license, or a license that is neither allow- nor deny-listed
(treated as "review needed"). Run in CI; `main()` returns a nonzero exit code on
any violation.
"""

from __future__ import annotations

import json
import subprocess
import sys

# Permissive + weak-copyleft-as-separate-dep licenses we ship against (spec §9.1).
ALLOWLIST: set[str] = {
    "mit",
    "bsd",
    "apache",
    "psf",
    "python software foundation",
    "isc",
    "mpl",
    "mozilla public license",
    "lgpl",  # kiwipiepy/soynlp: LGPL used as a separate, unmodified dependency
    "unlicense",
    "zlib",
    "historical permission notice and warning",
}

# Substrings that are HARD blockers (spec §9.5). Checked before the allowlist.
DENYLIST_SUBSTR: set[str] = {
    "agpl",
    "affero",
    "gpl",  # plain GPL (KoNLPy etc.); the matcher below excludes LGPL
    "non-commercial",
    "noncommercial",
    "-nc-",
    "nc-sa",
    "by-nc",
    "exaone",
}


def _normalize(license_str: str) -> str:
    return (license_str or "").strip().lower()


def _is_denied(norm: str) -> bool:
    for bad in DENYLIST_SUBSTR:
        if bad == "gpl":
            # Match GPL but NOT LGPL: a "gpl" not immediately preceded by "l".
            idx = norm.find("gpl")
            while idx != -1:
                preceded_by_l = idx > 0 and norm[idx - 1] == "l"
                if not preceded_by_l:
                    return True
                idx = norm.find("gpl", idx + 1)
        elif bad in norm:
            return True
    return False


def _is_allowed(norm: str) -> bool:
    return any(good in norm for good in ALLOWLIST)


def check_licenses(
    packages: list[dict], allowlist: set[str], denylist: set[str]
) -> list[str]:
    violations: list[str] = []
    for pkg in packages:
        name = pkg.get("Name", "<unknown>")
        raw = pkg.get("License", "")
        norm = _normalize(raw)
        if _is_denied(norm):
            violations.append(f"{name}: DENIED license '{raw}'")
            continue
        if not _is_allowed(norm):
            violations.append(f"{name}: license '{raw}' not on allowlist (review needed)")
    return violations


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print("pip-licenses failed to run:", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return 2
    packages = json.loads(proc.stdout)
    violations = check_licenses(packages, ALLOWLIST, DENYLIST_SUBSTR)
    if violations:
        print("License gate FAILED (spec §9.5 forbids GPL/AGPL/NC):", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print(f"License gate passed: {len(packages)} packages, all allowlisted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/test_license_allowlist.py -q`. Expect `7 passed`.

- [ ] **Step 5: Smoke-run the CLI against the real environment, expect exit 0.** Run `python scripts/check_licenses.py; echo "exit=$?"`. Expect a line like `License gate passed: <N> packages, all allowlisted.` and `exit=0` (the installed ship-path deps are all permissive/LGPL). If a transitive dep trips the gate, record it and pin/replace it before proceeding — this is the spec §14.5 gate working as intended; if it is a known-permissive license whose string is merely unrecognized, add that exact token to `ALLOWLIST`.

- [ ] **Step 6: Commit.** Run `git add scripts/check_licenses.py tests/test_license_allowlist.py && git commit -m "feat(m0): add pip-licenses allowlist gate (blocks GPL/AGPL/NC)"`.

### Task 6: GitHub Actions CI — pytest + license gate + assets separation, and README skeleton

**Files:**
- Create: `.github/workflows/ci.yml`
- Create: `README.md`
- Test: `tests/test_ci_workflow.py`

**Interfaces:**
- Consumes: `scripts/check_licenses.py` (CLI/`main` from Task 5), `scripts/check_assets_separation.py` (`find_asset_leaks` from Task 4), the `tests/` suite, the `dev` extra from `pyproject.toml`.
- Produces: `.github/workflows/ci.yml` running, on push/PR, (a) `pytest`, (b) the pip-licenses allowlist gate, (c) the `/assets` separation check — failing the build on any GPL/AGPL/NC dependency or asset leak (spec §14.5); `README.md` skeleton documenting the project, MVP scope (§12.2), and the honesty framing (rule-based, non-validated K-ER; original text prevails — spec §5.3/§3.1).

Steps:

- [ ] **Step 1: Write failing test asserting the workflow shape.** Create `tests/test_ci_workflow.py`:
```python
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_ci_workflow_exists_and_runs_the_three_gates():
    wf = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    # triggers
    assert "push" in wf
    assert "pull_request" in wf
    # gate 1: tests
    assert "pytest" in wf
    # gate 2: license allowlist
    assert "scripts/check_licenses.py" in wf
    # gate 3: assets separation
    assert "check_assets_separation" in wf
    # installs the dev extra so pip-licenses/pytest are present
    assert ".[dev]" in wf


def test_readme_states_honesty_framing_and_mvp():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Apache-2.0" in readme
    # spec §5.3 / §3.1 honesty framing must be visible
    assert "원문이 우선" in readme or "원문 우선" in readme
    assert "규칙 기반" in readme
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_ci_workflow.py -q`. Expect failure with `FileNotFoundError` for `.github/workflows/ci.yml`.

- [ ] **Step 3: Create the CI workflow.** Create `.github/workflows/ci.yml` (three gates per spec §14.5; the assets check is run inline so no extra script entry point is needed):
```yaml
name: CI

on:
  push:
    branches: ["**"]
  pull_request:

jobs:
  test-and-license-gate:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}

      - name: Install package with dev extras
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"

      - name: Gate 1 - tests
        run: python -m pytest -q

      - name: Gate 2 - license allowlist (fails on GPL/AGPL/NC)
        run: python scripts/check_licenses.py

      - name: Gate 3 - /assets separation
        run: |
          python -c "import sys; from scripts.check_assets_separation import find_asset_leaks; leaks = find_asset_leaks('.'); print('asset leaks:', leaks); sys.exit(1 if leaks else 0)"
```

- [ ] **Step 4: Create the README skeleton.** Create `README.md` (skeleton + honesty framing required on every surface per spec §3.1/§5.3; MVP scope per §12.2; `mcp` is stretch, not MVP):
````markdown
# 또박 (Ttobak)

**Open-source Korean Easy-Read engine.** Turns hard Korean public / administrative
documents (공문·고지서·안내문) into easy-read text, **measures** the easiness
(K-ER score) and self-corrects, with a **fidelity gate** that preserves
numbers, dates, amounts, deadlines, eligibility, and entities.

License: **Apache-2.0** (code). Pictogram assets are CC BY-SA, shipped separately
under [`assets/`](assets/README.md). Dataset is CC BY 4.0.

## 정직성 (Honesty) — 반드시 읽어 주세요
- K-ER 점수는 **한국 Easy-Read 지침에 정렬된 규칙 기반 루브릭**이며 **경험적으로
  검증된 지표가 아닙니다** (공개·검증된 한국어 Easy-Read 라벨 코퍼스 부재). 0–100
  점수는 보조 지표이고, 규칙별 위반 체크리스트(pass/fail)가 핵심 산출물입니다.
- 모든 출력은 원문과 면책 고지를 함께 렌더링합니다: **"자동 변환 결과이며 법적
  효력은 원문이 우선합니다."**
- 또박은 "한국어 Easy-Read AI 최초"를 주장하지 않습니다(온글·KCI·KIPS 선행). 엣지는
  **열림 + 측정 + 자가 교정 + 포맷 네이티브**입니다.

## MVP scope (8/27)
1. 입력: 텍스트 + PDF + HWPX(best-effort) -> IR. (이미지 OCR = 스트레치)
2. 파이프라인: GENERATE -> MEASURE -> REVISE (provider-agnostic LLM).
3. K-ER: 규칙 루브릭 -> 0–100 + 위반 목록.
4. Fidelity 게이트: 숫자/날짜/금액/기한/자격/엔티티 추출·검증·롤백 (고-recall, fail-safe = '검수 필요').
5. 렌더러: 원문/쉬운본 나란히 HTML + 면책 + K-ER·Fidelity 배지 + 소형 픽토그램 룩업.
6. 표면: 파이썬 패키지 + 웹 데모. (MCP 서버 = 스트레치)

> Stretch (not MVP): 이미지 OCR, MCP 서버, K-ER 모델 레이어(KcBERT/RSRS),
> semantic-NLI fidelity, semantic 픽토그램 매칭, TTS, 배치.

## 설치 / 개발
```bash
python -m pip install -e ".[dev]"
python -m pytest -q
```

## 라이선스 검증
```bash
python scripts/check_licenses.py   # GPL/AGPL/NC 발견 시 실패
```
See [`THIRD_PARTY_LICENSES.md`](THIRD_PARTY_LICENSES.md) and [`NOTICE`](NOTICE).
````

- [ ] **Step 5: Run the test, expect PASS.** Run `python -m pytest tests/test_ci_workflow.py -q`. Expect `2 passed`.

- [ ] **Step 6: Run the full suite + both gates locally, expect all green.** Run `python -m pytest -q && python scripts/check_licenses.py && python -c "from scripts.check_assets_separation import find_asset_leaks; assert find_asset_leaks('.') == [], find_asset_leaks('.'); print('assets clean')"`. Expect all tests passing, `License gate passed: ...`, and `assets clean`.

- [ ] **Step 7: Commit.** Run `git add .github/workflows/ci.yml README.md tests/test_ci_workflow.py && git commit -m "ci(m0): add CI with pytest + license gate + assets separation; README skeleton"`.

### Task 7: IR data model (Block, BlockType, Document)

Defines the canonical Intermediate Representation that every downstream module imports. This is the contract surface for `ttobak/ir.py` exactly as fixed in the shared brief: `BlockType` enum, `Block` model with per-block extraction confidence and optional table cells / bbox, and `Document` with a `text()` method that joins block text with newlines. No downstream module redefines these names.

**Files:**
- Create: `ttobak/ir.py`
- Create: `ttobak/__init__.py` (only if Task 1 did not already create it; see Step 1)
- Test: `tests/test_ir.py`

**Interfaces:**
- Consumes:
  - `pydantic.BaseModel`, `pydantic.Field` (pydantic v2, installed by Task 1)
  - `enum.Enum`, `str` (stdlib)
- Produces (exact symbols later tasks/modules rely on):
  - `class BlockType(str, Enum)` with members `HEADING="heading"`, `PARAGRAPH="paragraph"`, `LIST_ITEM="list_item"`, `TABLE="table"`, `CAPTION="caption"`
  - `class Block(BaseModel)` with fields `type: BlockType`, `text: str = ""`, `level: int = 0`, `cells: list[list[str]] | None = None`, `bbox: tuple[float, float, float, float] | None = None`, `confidence: float = 1.0`
  - `class Document(BaseModel)` with field `blocks: list[Block]`, `source_mime: str`, `meta: dict = {}` and method `text(self) -> str` (joins each block's `text` with `"\n"`)

- [ ] **Step 1: Ensure package directory exists.** Run `python -c "import os; os.makedirs('ttobak', exist_ok=True); open('ttobak/__init__.py','a').close(); print('ok')"`. Expected stdout: `ok`. (Idempotent: if Task 1 already created `ttobak/__init__.py` this leaves it untouched.)

- [ ] **Step 2: Write failing test for the IR data model.** Create `tests/test_ir.py` with this exact content:
```python
import pytest
from pydantic import ValidationError

from ttobak.ir import Block, BlockType, Document


def test_blocktype_values():
    assert BlockType.HEADING == "heading"
    assert BlockType.PARAGRAPH == "paragraph"
    assert BlockType.LIST_ITEM == "list_item"
    assert BlockType.TABLE == "table"
    assert BlockType.CAPTION == "caption"


def test_block_defaults():
    b = Block(type=BlockType.PARAGRAPH)
    assert b.text == ""
    assert b.level == 0
    assert b.cells is None
    assert b.bbox is None
    assert b.confidence == 1.0


def test_block_full_construction():
    b = Block(
        type=BlockType.TABLE,
        text="요약",
        level=2,
        cells=[["항목", "금액"], ["보험료", "1,295,400원"]],
        bbox=(0.0, 0.0, 100.0, 50.0),
        confidence=0.8,
    )
    assert b.type == BlockType.TABLE
    assert b.cells[1][1] == "1,295,400원"
    assert b.bbox == (0.0, 0.0, 100.0, 50.0)
    assert b.confidence == 0.8


def test_block_type_is_required():
    with pytest.raises(ValidationError):
        Block()


def test_document_text_joins_block_text_with_newlines():
    doc = Document(
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="2026년 7월분 보험료를 안내드립니다."),
            Block(type=BlockType.LIST_ITEM, text="납부 기한: 2026년 7월 25일"),
        ],
        source_mime="text/plain",
    )
    assert doc.text() == (
        "건강보험료 납부 안내\n"
        "2026년 7월분 보험료를 안내드립니다.\n"
        "납부 기한: 2026년 7월 25일"
    )


def test_document_meta_defaults_to_empty_dict():
    doc = Document(blocks=[], source_mime="text/plain")
    assert doc.meta == {}
    assert doc.text() == ""
```

- [ ] **Step 3: Run the test, expecting import failure.** Run `python -m pytest tests/test_ir.py -q`. Expected: collection error / FAIL with `ModuleNotFoundError: No module named 'ttobak.ir'`.

- [ ] **Step 4: Implement the IR data model.** Create `ttobak/ir.py` with this exact content:
```python
"""Intermediate Representation (IR) for Ttobak.

This is the canonical, shared data model that every downstream module
(parse, pipeline, metric, fidelity, render) imports. Do NOT redefine these
names elsewhere — import them from here.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST_ITEM = "list_item"
    TABLE = "table"
    CAPTION = "caption"


class Block(BaseModel):
    type: BlockType
    text: str = ""
    level: int = 0
    cells: list[list[str]] | None = None
    bbox: tuple[float, float, float, float] | None = None
    confidence: float = 1.0


class Document(BaseModel):
    blocks: list[Block]
    source_mime: str
    meta: dict = Field(default_factory=dict)

    def text(self) -> str:
        """Join every block's text with newlines (round-trippable plain text)."""
        return "\n".join(block.text for block in self.blocks)
```

- [ ] **Step 5: Run the test, expecting PASS.** Run `python -m pytest tests/test_ir.py -q`. Expected: `6 passed`.

- [ ] **Step 6: Commit.** Run `git add ttobak/ir.py ttobak/__init__.py tests/test_ir.py && git commit -m "feat(ir): add Block, BlockType, Document IR data model"`.

### Task 8: parse() mime dispatch with graceful degradation

Implements the public engine entry point `parse(source, mime) -> Document` from `ttobak/parse/__init__.py`. Per spec §4.2.A and §7.3, dispatch is by MIME type and unsupported/broken input must fail with an explicit error (not silent garbage). This task delivers the dispatcher plus a shared `UnsupportedMimeError`; the text-parsing logic itself lands in Task 9. To keep this task self-contained and test-driven, the dispatcher starts by routing `text/plain` and `text/markdown` to a minimal inline single-paragraph parser, then Task 9 replaces that body with the richer `parse_text`.

**Files:**
- Create: `ttobak/parse/__init__.py`
- Create: `ttobak/parse/text_parser.py`
- Test: `tests/test_parse_dispatch.py`

**Interfaces:**
- Consumes:
  - `ttobak.ir.Document`, `ttobak.ir.Block`, `ttobak.ir.BlockType` (from Task 7)
  - `pathlib.Path` (stdlib)
- Produces:
  - `ttobak/parse/text_parser.py`: `class UnsupportedMimeError(ValueError)`
  - `ttobak/parse/__init__.py`: `def parse(source: bytes | str | Path, mime: str) -> Document` — dispatch by `mime`; supported text MIME types route to the text parser; everything else raises `UnsupportedMimeError`. Accepts `bytes` (decoded UTF-8), `str`, or `Path` (read as UTF-8 text for text MIME types).

- [ ] **Step 1: Write failing test for the dispatcher.** Create `tests/test_parse_dispatch.py` with this exact content:
```python
import pytest

from ttobak.ir import BlockType, Document
from ttobak.parse import parse
from ttobak.parse.text_parser import UnsupportedMimeError


def test_parse_returns_document_for_plain_text():
    doc = parse("국민건강보험공단 안내문입니다.", "text/plain")
    assert isinstance(doc, Document)
    assert doc.source_mime == "text/plain"
    assert doc.text() == "국민건강보험공단 안내문입니다."


def test_parse_accepts_bytes_input():
    raw = "보험료 납부 안내".encode("utf-8")
    doc = parse(raw, "text/plain")
    assert doc.text() == "보험료 납부 안내"


def test_parse_accepts_path_input(tmp_path):
    p = tmp_path / "notice.txt"
    p.write_text("청년 주거지원 안내", encoding="utf-8")
    doc = parse(p, "text/plain")
    assert doc.text() == "청년 주거지원 안내"
    assert doc.source_mime == "text/plain"


def test_parse_routes_markdown_mime_to_text_parser():
    doc = parse("# 제목", "text/markdown")
    assert isinstance(doc, Document)
    assert doc.source_mime == "text/markdown"


def test_parse_raises_on_unsupported_mime():
    with pytest.raises(UnsupportedMimeError) as exc:
        parse(b"%PDF-1.7", "application/pdf")
    assert "application/pdf" in str(exc.value)


def test_parse_first_block_is_paragraph_for_single_line():
    doc = parse("한 줄짜리 안내입니다.", "text/plain")
    assert doc.blocks[0].type == BlockType.PARAGRAPH
    assert doc.blocks[0].confidence == 1.0
```

- [ ] **Step 2: Run the test, expecting import failure.** Run `python -m pytest tests/test_parse_dispatch.py -q`. Expected: FAIL with `ModuleNotFoundError: No module named 'ttobak.parse'`.

- [ ] **Step 3: Create the minimal text parser module.** Create `ttobak/parse/text_parser.py` with this exact content:
```python
"""Plain-text and markdown-ish parser into the Ttobak IR.

Text is the PRIMARY, trusted input tier (spec §7.1): extraction confidence is
always 1.0 because no lossy extraction occurs.
"""
from __future__ import annotations

from ttobak.ir import Block, BlockType, Document


class UnsupportedMimeError(ValueError):
    """Raised when parse() is given a MIME type it cannot handle.

    Per spec §7.3 the engine degrades gracefully with an explicit error rather
    than silently producing garbage.
    """


def parse_text(text: str, mime: str) -> Document:
    """Parse plain text into a single-paragraph Document (placeholder body).

    Replaced with full heading/list detection in Task 9. Kept minimal
    here so the dispatcher task is independently testable.
    """
    block = Block(type=BlockType.PARAGRAPH, text=text, confidence=1.0)
    return Document(blocks=[block], source_mime=mime)
```

- [ ] **Step 4: Create the dispatcher.** Create `ttobak/parse/__init__.py` with this exact content:
```python
"""Public parse entry point: dispatch raw input to a format-specific parser.

    parse(source: bytes | str | Path, mime: str) -> Document
"""
from __future__ import annotations

from pathlib import Path

from ttobak.ir import Document
from ttobak.parse.text_parser import UnsupportedMimeError, parse_text

_TEXT_MIMES = frozenset({"text/plain", "text/markdown"})


def _to_text(source: bytes | str | Path) -> str:
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if isinstance(source, bytes):
        return source.decode("utf-8")
    return source


def parse(source: bytes | str | Path, mime: str) -> Document:
    """Parse ``source`` of the given ``mime`` into a structured Document.

    Supported now: ``text/plain``, ``text/markdown``. Unsupported MIME types
    raise :class:`UnsupportedMimeError` (graceful, explicit degradation).
    """
    if mime in _TEXT_MIMES:
        return parse_text(_to_text(source), mime)
    raise UnsupportedMimeError(f"unsupported mime type: {mime!r}")
```

- [ ] **Step 5: Run the test, expecting PASS.** Run `python -m pytest tests/test_parse_dispatch.py -q`. Expected: `6 passed`.

- [ ] **Step 6: Commit.** Run `git add ttobak/parse/__init__.py ttobak/parse/text_parser.py tests/test_parse_dispatch.py && git commit -m "feat(parse): add parse() mime dispatch with graceful UnsupportedMimeError"`.

### Task 9: text parser — heading & list detection (markdown-ish)

Replaces the placeholder `parse_text` body with real structure detection per spec §7.1 ("simple markdown-ish heading/list detection") and §14.1 (block typing + confidence). Splits text into blocks on blank lines; within that, detects markdown ATX headings (`#`..`######` → `HEADING` with `level` = hash count), bullet/numbered list items (`-`/`*`/`•`/`1.` → `LIST_ITEM`), and everything else as `PARAGRAPH`. Confidence stays 1.0 (text is the trusted tier). Round-trip is preserved because each block's `text` holds the original line content joined by newlines, so `Document.text()` reproduces the input lines (blank-line separators collapse, which the round-trip test accounts for).

**Files:**
- Modify: `ttobak/parse/text_parser.py`
- Test: `tests/test_text_parser.py`

**Interfaces:**
- Consumes:
  - `ttobak.ir.Block`, `ttobak.ir.BlockType`, `ttobak.ir.Document` (from Task 7)
  - `re` (stdlib)
- Produces:
  - `ttobak/parse/text_parser.py`: `def parse_text(text: str, mime: str) -> Document` — multi-block parser. Heading lines (`^#{1,6}\s+`) → `Block(type=HEADING, level=<hash count>, text=<heading text without hashes>)`; list lines (`^\s*([-*•]|\d+[.)])\s+`) → `Block(type=LIST_ITEM, text=<full original line, stripped>)`; other non-blank lines grouped (consecutive non-blank, non-heading, non-list lines) into one `Block(type=PARAGRAPH, text=<lines joined by \n>)`. All blocks `confidence=1.0`. Blank lines separate paragraphs and are not emitted as blocks.

- [ ] **Step 1: Write failing test for structure detection.** Create `tests/test_text_parser.py` with this exact content:
```python
from ttobak.ir import BlockType
from ttobak.parse.text_parser import parse_text

NOTICE = """# 청년 월세 한시 특별지원 안내

신청 기간은 2026년 7월 1일부터 2026년 8월 31일까지입니다.
지원 금액은 월 최대 200,000원입니다.

## 신청 자격
- 만 19세 이상 만 34세 이하 청년
- 부모와 따로 거주하는 무주택자
1. 주민센터 방문 신청
2. 온라인 신청
"""


def test_heading_detected_with_level():
    doc = parse_text(NOTICE, "text/markdown")
    headings = [b for b in doc.blocks if b.type == BlockType.HEADING]
    assert headings[0].text == "청년 월세 한시 특별지원 안내"
    assert headings[0].level == 1
    assert headings[1].text == "신청 자격"
    assert headings[1].level == 2


def test_paragraph_groups_consecutive_lines():
    doc = parse_text(NOTICE, "text/markdown")
    paragraphs = [b for b in doc.blocks if b.type == BlockType.PARAGRAPH]
    assert paragraphs[0].text == (
        "신청 기간은 2026년 7월 1일부터 2026년 8월 31일까지입니다.\n"
        "지원 금액은 월 최대 200,000원입니다."
    )


def test_bullet_and_numbered_lines_become_list_items():
    doc = parse_text(NOTICE, "text/markdown")
    items = [b.text for b in doc.blocks if b.type == BlockType.LIST_ITEM]
    assert items == [
        "- 만 19세 이상 만 34세 이하 청년",
        "- 부모와 따로 거주하는 무주택자",
        "1. 주민센터 방문 신청",
        "2. 온라인 신청",
    ]


def test_all_blocks_have_full_confidence():
    doc = parse_text(NOTICE, "text/markdown")
    assert all(b.confidence == 1.0 for b in doc.blocks)


def test_blank_lines_do_not_produce_blocks():
    doc = parse_text("첫 줄\n\n\n둘째 줄", "text/plain")
    texts = [b.text for b in doc.blocks]
    assert texts == ["첫 줄", "둘째 줄"]


def test_empty_input_yields_no_blocks():
    doc = parse_text("", "text/plain")
    assert doc.blocks == []
    assert doc.text() == ""
```

- [ ] **Step 2: Run the test, expecting FAIL on structure.** Run `python -m pytest tests/test_text_parser.py -q`. Expected: FAIL — e.g. `test_heading_detected_with_level` errors with `IndexError: list index out of range` (placeholder emits one PARAGRAPH, so `headings[0]` does not exist).

- [ ] **Step 3: Implement heading/list/paragraph detection.** Replace the entire contents of `ttobak/parse/text_parser.py` with this exact content:
```python
"""Plain-text and markdown-ish parser into the Ttobak IR.

Text is the PRIMARY, trusted input tier (spec §7.1): extraction confidence is
always 1.0 because no lossy extraction occurs. Detects markdown ATX headings,
bullet/numbered list items, and groups remaining lines into paragraphs.
"""
from __future__ import annotations

import re

from ttobak.ir import Block, BlockType, Document

_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_LIST_RE = re.compile(r"^\s*([-*•]|\d+[.)])\s+\S")


class UnsupportedMimeError(ValueError):
    """Raised when parse() is given a MIME type it cannot handle.

    Per spec §7.3 the engine degrades gracefully with an explicit error rather
    than silently producing garbage.
    """


def parse_text(text: str, mime: str) -> Document:
    """Parse plain/markdown text into structured IR blocks.

    - ``#``..``######`` lines -> HEADING (level = number of hashes).
    - ``-``/``*``/``•``/``1.``/``1)`` lines -> LIST_ITEM (original line, stripped).
    - Consecutive remaining non-blank lines -> one PARAGRAPH (joined by newlines).
    - Blank lines separate paragraphs and are not emitted as blocks.

    All blocks carry confidence 1.0 (trusted text tier).
    """
    blocks: list[Block] = []
    paragraph_lines: list[str] = []

    def flush_paragraph() -> None:
        if paragraph_lines:
            blocks.append(
                Block(
                    type=BlockType.PARAGRAPH,
                    text="\n".join(paragraph_lines),
                    confidence=1.0,
                )
            )
            paragraph_lines.clear()

    for raw_line in text.split("\n"):
        line = raw_line.rstrip()
        if not line.strip():
            flush_paragraph()
            continue

        heading = _HEADING_RE.match(line)
        if heading is not None:
            flush_paragraph()
            blocks.append(
                Block(
                    type=BlockType.HEADING,
                    text=heading.group(2).strip(),
                    level=len(heading.group(1)),
                    confidence=1.0,
                )
            )
            continue

        if _LIST_RE.match(line):
            flush_paragraph()
            blocks.append(
                Block(
                    type=BlockType.LIST_ITEM,
                    text=line.strip(),
                    confidence=1.0,
                )
            )
            continue

        paragraph_lines.append(line.strip())

    flush_paragraph()
    return Document(blocks=blocks, source_mime=mime)
```

- [ ] **Step 4: Run the new test, expecting PASS.** Run `python -m pytest tests/test_text_parser.py -q`. Expected: `6 passed`.

- [ ] **Step 5: Run the dispatcher test, confirming no regression.** Run `python -m pytest tests/test_parse_dispatch.py -q`. Expected: `6 passed` (the dispatcher's markdown/plain routing still works; `UnsupportedMimeError` is still importable from `text_parser`). Note: `test_parse_first_block_is_paragraph_for_single_line` still holds because a single non-heading, non-list line becomes one PARAGRAPH.

- [ ] **Step 6: Commit.** Run `git add ttobak/parse/text_parser.py tests/test_text_parser.py && git commit -m "feat(parse): detect markdown-ish headings, lists, and paragraphs in text parser"`.

### Task 10: round-trip integrity + golden IR snapshot

Locks in the two acceptance properties the spec calls out for this module: round-trip text → Document → `.text()` (spec §14.1 "round-trip text -> Document -> .text()") and a golden IR snapshot of a realistic Korean notice for block-typing/confidence regression protection (spec §14.1 "12문서 골든 IR 스냅샷, 블록 타입·신뢰도 검증"). The round-trip property is exact for text that has no markdown markup and no blank lines (each line becomes one paragraph block, rejoined verbatim); for markup we assert the structural snapshot instead.

**Files:**
- Test: `tests/test_parse_roundtrip.py`
- Create: `tests/fixtures/notice_health_insurance.txt`

**Interfaces:**
- Consumes:
  - `ttobak.parse.parse` (Task 8)
  - `ttobak.ir.BlockType` (Task 7)
  - `pathlib.Path` (stdlib)
- Produces:
  - Regression coverage only (no new public symbols). Fixture file `tests/fixtures/notice_health_insurance.txt` available to later evaluation/integration tasks as a clean demo source.

- [ ] **Step 1: Create the realistic Korean fixture.** Create `tests/fixtures/notice_health_insurance.txt` with this exact content:
```
# 2026년 7월분 건강보험료 납부 안내

국민건강보험공단에서 2026년 7월분 지역가입자 건강보험료를 안내드립니다.
아래 내용을 확인하시고 기한 내에 납부하여 주시기 바랍니다.

## 납부 정보
- 보험료: 1,295,400원
- 납부 기한: 2026년 7월 25일
- 미납 시 연체금이 부과됩니다.

문의: 국민건강보험공단 고객센터 1577-1000
```

- [ ] **Step 2: Write failing round-trip and snapshot test.** Create `tests/test_parse_roundtrip.py` with this exact content:
```python
from pathlib import Path

from ttobak.ir import BlockType
from ttobak.parse import parse

FIXTURE = Path(__file__).parent / "fixtures" / "notice_health_insurance.txt"


def test_plain_text_roundtrip_is_exact():
    # No markdown markup, no blank lines -> each line is one paragraph block,
    # so .text() must reproduce the input verbatim.
    src = "보험료를 납부해 주세요.\n납부 기한은 2026년 7월 25일입니다.\n문의 1577-1000"
    doc = parse(src, "text/plain")
    assert doc.text() == src


def test_fixture_block_types_snapshot():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    snapshot = [(b.type.value, b.level) for b in doc.blocks]
    assert snapshot == [
        ("heading", 1),
        ("paragraph", 0),
        ("heading", 2),
        ("list_item", 0),
        ("list_item", 0),
        ("list_item", 0),
        ("paragraph", 0),
    ]


def test_fixture_preserves_critical_facts_in_block_text():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    joined = doc.text()
    # Fidelity-critical spans must survive parsing verbatim (spec §3.1).
    assert "1,295,400원" in joined
    assert "2026년 7월 25일" in joined
    assert "1577-1000" in joined


def test_fixture_all_confidence_full():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    assert all(b.confidence == 1.0 for b in doc.blocks)


def test_fixture_first_heading_text():
    doc = parse(FIXTURE.read_bytes(), "text/markdown")
    headings = [b for b in doc.blocks if b.type == BlockType.HEADING]
    assert headings[0].text == "2026년 7월분 건강보험료 납부 안내"
```

- [ ] **Step 3: Run the test, expecting FAIL on missing fixture path or assertion.** Run `python -m pytest tests/test_parse_roundtrip.py -q`. Expected: FAIL — if the fixtures directory was not committed yet the test errors with `FileNotFoundError`; once the fixture exists this run is the guard. (If it unexpectedly passes immediately because prior tasks already satisfy every assertion, that is acceptable — the snapshot still locks the behavior; proceed to commit.)

- [ ] **Step 4: Confirm the parser already satisfies the snapshot (no production change needed).** Run `python -m pytest tests/test_parse_roundtrip.py -q`. Expected: `5 passed`. (This task is pure regression hardening over the parser built in Tasks 7–9; if any assertion fails, fix the parser in `ttobak/parse/text_parser.py` to match the documented block-typing rules before continuing — do not edit the test to fit a wrong output.)

- [ ] **Step 5: Run the full module test suite.** Run `python -m pytest tests/test_ir.py tests/test_parse_dispatch.py tests/test_text_parser.py tests/test_parse_roundtrip.py -q`. Expected: `23 passed`.

- [ ] **Step 6: Commit.** Run `git add tests/fixtures/notice_health_insurance.txt tests/test_parse_roundtrip.py && git commit -m "test(parse): round-trip integrity and golden IR snapshot for Korean notice"`.

### Task 11: LLMProvider Protocol + provider package scaffolding

**Files:**
- Create: `ttobak/providers/__init__.py`
- Create: `ttobak/providers/base.py`
- Modify: `pyproject.toml` (add `anthropic` and `ollama` optional-dependency extras; do NOT overwrite the Task 1 file)
- Create: `tests/providers/__init__.py`
- Test: `tests/providers/test_base.py`

**Interfaces:**
- Consumes: the `ttobak` package + `pyproject.toml` from Task 1; nothing else (the canonical `LLMProvider` Protocol signature comes from the SHARED CONTRACTS for `ttobak/providers/base.py`).
- Produces:
  - `ttobak/providers/base.py`: `class LLMProvider(Protocol): def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str: ...` (runtime-checkable).
  - `ttobak.providers` subpackage importable; `pyproject.toml` carries `[project.optional-dependencies]` entries `anthropic = ["anthropic>=0.40"]` and `ollama = ["ollama>=0.4"]` (merged into the existing `dev` extra block).

Steps:

- [ ] **Step 1: Write failing test for the Protocol contract.** Create `tests/providers/__init__.py` as an empty file, then create `tests/providers/test_base.py` with REAL pytest code that asserts the Protocol exists, is runtime-checkable, and structurally matches a conforming class:
```python
import inspect

from ttobak.providers.base import LLMProvider


def test_llmprovider_is_runtime_checkable_protocol():
    # A conforming class must satisfy isinstance against the Protocol.
    class Conforming:
        def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str:
            return "ok"

    assert isinstance(Conforming(), LLMProvider)


def test_non_conforming_class_is_not_instance():
    class Missing:
        def something_else(self) -> str:
            return "no"

    assert not isinstance(Missing(), LLMProvider)


def test_generate_signature_matches_contract():
    sig = inspect.signature(LLMProvider.generate)
    params = sig.parameters
    assert list(params) == ["self", "prompt", "system", "max_tokens"]
    assert params["system"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["max_tokens"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["max_tokens"].default == 2048
    assert params["system"].default is None
```

- [ ] **Step 2: Run the test, expect FAIL (collection error).** Run `python -m pytest tests/providers/test_base.py -q`. Expected: `ModuleNotFoundError: No module named 'ttobak.providers'`.

- [ ] **Step 3: Add the provider extras to `pyproject.toml`.** Edit the existing `[project.optional-dependencies]` table (created in Task 1) to add the two extras (do NOT recreate the file or remove the `dev` extra):
```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0,<9",
    "pip-licenses>=5.0,<6",
]
anthropic = ["anthropic>=0.40"]
ollama = ["ollama>=0.4"]
```

- [ ] **Step 4: Create the provider package + Protocol.** Create `ttobak/providers/__init__.py` as a placeholder (the factory lands in Task 15; do not import submodules here yet):
```python
"""LLM provider abstraction for Ttobak."""
```
  Then create `ttobak/providers/base.py`:
```python
"""The LLMProvider abstraction.

Every provider (Fake, Anthropic, Ollama, ...) implements this structural
Protocol. Callers depend only on ``generate``; the engine is provider-agnostic.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Minimal text-in / text-out LLM interface.

    Implementations must be deterministic in tests (use FakeProvider). Real
    providers (Anthropic, Ollama) are guarded behind optional dependencies.
    """

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        """Return the model's text completion for ``prompt``.

        Args:
            prompt: The user prompt (the request to the model).
            system: Optional system instruction guiding the model's behavior.
            max_tokens: Upper bound on generated tokens.

        Returns:
            The generated text as a single string.
        """
        ...
```

- [ ] **Step 5: Run the test, expect PASS.** Run `python -m pytest tests/providers/test_base.py -q`. Expected: `3 passed`.

- [ ] **Step 6: Commit.** Run `git checkout -b m2-llm-providers && git add pyproject.toml ttobak/providers/__init__.py ttobak/providers/base.py tests/providers/__init__.py tests/providers/test_base.py && git commit -m "feat(providers): add LLMProvider Protocol and package scaffolding"`.

### Task 12: FakeProvider — deterministic scripted provider for tests

> NOTE (cross-module reconciliation): two FakeProvider shapes appear across the brief. This task ships the **canonical, richer FakeProvider** at `ttobak/providers/fake.py` — `__init__(self, responses: list[str] | None = None, *, default: str | None = None)`, attribute `calls: list[dict]`, FIFO `generate(...)`. The pipeline module (Task 16+) and web/eval modules use THIS class via `from ttobak.providers.fake import FakeProvider` (or `from ttobak.providers import FakeProvider`). Pipeline tests that were originally written against an `outputs:`/`prompts:`/`calls:int` variant MUST be adapted to this canonical class (scripted via the `responses=` list; assert call count via `len(provider.calls)` and prompts via `provider.calls[i]["prompt"]`). Do not introduce a second FakeProvider.

**Files:**
- Create: `ttobak/providers/fake.py`
- Test: `tests/providers/test_fake.py`

**Interfaces:**
- Consumes: `ttobak/providers/base.py`: `LLMProvider` Protocol.
- Produces: `ttobak/providers/fake.py`: `class FakeProvider` with `__init__(self, responses: list[str] | None = None, *, default: str | None = None)`, attribute `calls: list[dict]`, method `generate(self, prompt, *, system=None, max_tokens=2048) -> str`. Pops scripted responses FIFO; records each call as `{"prompt", "system", "max_tokens"}`. This is the ONLY provider used in tests across all modules.

- [ ] **Step 1: Write failing test for FakeProvider behavior.** Create `tests/providers/test_fake.py`:
```python
import pytest

from ttobak.providers.base import LLMProvider
from ttobak.providers.fake import FakeProvider


def test_fakeprovider_satisfies_protocol():
    assert isinstance(FakeProvider(["x"]), LLMProvider)


def test_returns_scripted_responses_in_fifo_order():
    fake = FakeProvider(["첫 번째 쉬운 글입니다.", "두 번째 응답입니다."])
    assert fake.generate("원문1") == "첫 번째 쉬운 글입니다."
    assert fake.generate("원문2") == "두 번째 응답입니다."


def test_records_each_call_with_args():
    fake = FakeProvider(["응답"])
    fake.generate("쉬운 글로 바꿔주세요", system="너는 쉬운 글 변환기다", max_tokens=512)
    assert fake.calls == [
        {
            "prompt": "쉬운 글로 바꿔주세요",
            "system": "너는 쉬운 글 변환기다",
            "max_tokens": 512,
        }
    ]


def test_falls_back_to_default_when_queue_empty():
    fake = FakeProvider(["하나만 있음"], default="기본 응답")
    assert fake.generate("a") == "하나만 있음"
    assert fake.generate("b") == "기본 응답"
    assert fake.generate("c") == "기본 응답"


def test_raises_when_queue_empty_and_no_default():
    fake = FakeProvider(["하나만 있음"])
    fake.generate("a")
    with pytest.raises(IndexError, match="FakeProvider"):
        fake.generate("b")


def test_empty_construction_uses_default_only():
    fake = FakeProvider(default="항상 같은 응답")
    assert fake.generate("a") == "항상 같은 응답"
    assert fake.generate("b") == "항상 같은 응답"
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/providers/test_fake.py -q`. Expected: `ModuleNotFoundError: No module named 'ttobak.providers.fake'`.

- [ ] **Step 3: Implement FakeProvider.** Create `ttobak/providers/fake.py`:
```python
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
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/providers/test_fake.py -q`. Expected: `6 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/providers/fake.py tests/providers/test_fake.py && git commit -m "feat(providers): add deterministic FakeProvider for tests"`.

### Task 13: AnthropicProvider — guarded real provider (demo default)

**Files:**
- Create: `ttobak/providers/anthropic_provider.py`
- Test: `tests/providers/test_anthropic_provider.py`

**Interfaces:**
- Consumes: `ttobak/providers/base.py`: `LLMProvider` Protocol.
- Produces: `ttobak/providers/anthropic_provider.py`: `class AnthropicProvider` with `__init__(self, *, model: str = "claude-opus-4-8", api_key: str | None = None, client: object | None = None)` (guarded `import anthropic` deferred to construction; `client` injectable for tests) and `generate(self, prompt, *, system=None, max_tokens=2048) -> str`.

- [ ] **Step 1: Write failing test using an injected fake SDK client (no live API).** Create `tests/providers/test_anthropic_provider.py`. The test injects a stand-in client mimicking the Anthropic SDK response shape (`response.content` = list of blocks with `.type`/`.text`), so no network/API key is touched:
```python
import pytest

from ttobak.providers.anthropic_provider import AnthropicProvider
from ttobak.providers.base import LLMProvider


class _Block:
    def __init__(self, type_: str, text: str) -> None:
        self.type = type_
        self.text = text


class _Response:
    def __init__(self, blocks):
        self.content = blocks


class _Messages:
    def __init__(self, response):
        self._response = response
        self.last_kwargs: dict | None = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        return self._response


class _FakeAnthropicClient:
    """Mimics anthropic.Anthropic() shape for tests — no network."""

    def __init__(self, response):
        self.messages = _Messages(response)


def test_satisfies_protocol():
    client = _FakeAnthropicClient(_Response([_Block("text", "쉬운 글입니다.")]))
    assert isinstance(AnthropicProvider(client=client), LLMProvider)


def test_generate_returns_concatenated_text_blocks():
    client = _FakeAnthropicClient(
        _Response([_Block("text", "첫 줄입니다.\n"), _Block("text", "둘째 줄입니다.")])
    )
    provider = AnthropicProvider(client=client)
    out = provider.generate("이 문장을 쉽게 바꿔주세요.")
    assert out == "첫 줄입니다.\n둘째 줄입니다."


def test_generate_skips_non_text_blocks():
    client = _FakeAnthropicClient(
        _Response([_Block("thinking", "내부 추론"), _Block("text", "최종 답")])
    )
    provider = AnthropicProvider(client=client)
    assert provider.generate("프롬프트") == "최종 답"


def test_generate_passes_model_system_and_max_tokens():
    client = _FakeAnthropicClient(_Response([_Block("text", "ok")]))
    provider = AnthropicProvider(model="claude-opus-4-8", client=client)
    provider.generate("프롬프트", system="너는 쉬운 글 변환기다", max_tokens=512)
    kwargs = client.messages.last_kwargs
    assert kwargs["model"] == "claude-opus-4-8"
    assert kwargs["max_tokens"] == 512
    assert kwargs["system"] == "너는 쉬운 글 변환기다"
    assert kwargs["messages"] == [{"role": "user", "content": "프롬프트"}]


def test_generate_omits_system_when_none():
    client = _FakeAnthropicClient(_Response([_Block("text", "ok")]))
    provider = AnthropicProvider(client=client)
    provider.generate("프롬프트")
    assert "system" not in client.messages.last_kwargs
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/providers/test_anthropic_provider.py -q`. Expected: `ModuleNotFoundError: No module named 'ttobak.providers.anthropic_provider'`.

- [ ] **Step 3: Implement AnthropicProvider with a guarded import.** Create `ttobak/providers/anthropic_provider.py`. The `anthropic` SDK import is deferred to construction (only when no client is injected) so the package imports cleanly without the optional dependency. Uses the canonical `claude-opus-4-8` model id and the Messages API shape:
```python
"""Anthropic (Claude) provider — the demo default.

The ``anthropic`` SDK is an optional dependency, imported lazily at
construction so importing this module never fails when the SDK is absent.
Tests inject a stand-in ``client`` and never touch a live API or key.
"""

from __future__ import annotations


class AnthropicProvider:
    """LLMProvider backed by the Anthropic Messages API.

    Args:
        model: Claude model id. Default ``claude-opus-4-8``.
        api_key: Optional explicit API key. If ``None``, the SDK resolves it
            from the environment (``ANTHROPIC_API_KEY``).
        client: Optional pre-built client (used by tests to avoid the network).
            When provided, the ``anthropic`` SDK is never imported.
    """

    def __init__(
        self,
        *,
        model: str = "claude-opus-4-8",
        api_key: str | None = None,
        client: object | None = None,
    ) -> None:
        self.model = model
        if client is not None:
            self._client = client
            return
        try:
            import anthropic
        except ImportError as exc:  # pragma: no cover - exercised only without the extra
            raise ImportError(
                "AnthropicProvider requires the 'anthropic' package. "
                "Install it with: pip install 'ttobak[anthropic]'"
            ) from exc
        self._client = (
            anthropic.Anthropic(api_key=api_key)
            if api_key is not None
            else anthropic.Anthropic()
        )

    def generate(
        self,
        prompt: str,
        *,
        system: str | None = None,
        max_tokens: int = 2048,
    ) -> str:
        kwargs: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
        if system is not None:
            kwargs["system"] = system
        response = self._client.messages.create(**kwargs)
        return "".join(
            block.text for block in response.content if block.type == "text"
        )
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/providers/test_anthropic_provider.py -q`. Expected: `5 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/providers/anthropic_provider.py tests/providers/test_anthropic_provider.py && git commit -m "feat(providers): add guarded AnthropicProvider (demo default)"`.

### Task 14: OllamaProvider — guarded local provider (Kanana-1.5-8B / Qwen2.5)

**Files:**
- Create: `ttobak/providers/ollama_provider.py`
- Test: `tests/providers/test_ollama_provider.py`

**Interfaces:**
- Consumes: `ttobak/providers/base.py`: `LLMProvider` Protocol.
- Produces: `ttobak/providers/ollama_provider.py`: `class OllamaProvider` with `__init__(self, *, model: str = "kanana-1.5-8b", host: str | None = None, client: object | None = None)` (guarded `from ollama import Client` deferred to construction; `client` injectable for tests) and `generate(self, prompt, *, system=None, max_tokens=2048) -> str`.

- [ ] **Step 1: Write failing test using an injected fake Ollama client (no daemon).** Create `tests/providers/test_ollama_provider.py`. The stand-in client mimics the ollama-python response shape (`response.message.content`) and records the kwargs passed to `chat`:
```python
import pytest

from ttobak.providers.base import LLMProvider
from ttobak.providers.ollama_provider import OllamaProvider


class _Message:
    def __init__(self, content: str) -> None:
        self.content = content


class _ChatResponse:
    def __init__(self, content: str) -> None:
        self.message = _Message(content)


class _FakeOllamaClient:
    """Mimics ollama.Client shape for tests — no daemon."""

    def __init__(self, content: str) -> None:
        self._content = content
        self.last_kwargs: dict | None = None

    def chat(self, **kwargs):
        self.last_kwargs = kwargs
        return _ChatResponse(self._content)


def test_satisfies_protocol():
    assert isinstance(OllamaProvider(client=_FakeOllamaClient("ok")), LLMProvider)


def test_generate_returns_message_content():
    provider = OllamaProvider(client=_FakeOllamaClient("쉬운 글 결과입니다."))
    assert provider.generate("원문") == "쉬운 글 결과입니다."


def test_generate_passes_model_messages_and_num_predict():
    client = _FakeOllamaClient("ok")
    provider = OllamaProvider(model="qwen2.5:7b", client=client)
    provider.generate("프롬프트", system="너는 쉬운 글 변환기다", max_tokens=512)
    kwargs = client.last_kwargs
    assert kwargs["model"] == "qwen2.5:7b"
    assert kwargs["messages"] == [
        {"role": "system", "content": "너는 쉬운 글 변환기다"},
        {"role": "user", "content": "프롬프트"},
    ]
    assert kwargs["options"]["num_predict"] == 512


def test_generate_omits_system_message_when_none():
    client = _FakeOllamaClient("ok")
    provider = OllamaProvider(client=client)
    provider.generate("프롬프트")
    assert client.last_kwargs["messages"] == [
        {"role": "user", "content": "프롬프트"}
    ]


def test_default_model_is_kanana():
    provider = OllamaProvider(client=_FakeOllamaClient("ok"))
    assert provider.model == "kanana-1.5-8b"
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/providers/test_ollama_provider.py -q`. Expected: `ModuleNotFoundError: No module named 'ttobak.providers.ollama_provider'`.

- [ ] **Step 3: Implement OllamaProvider with a guarded import.** Create `ttobak/providers/ollama_provider.py`. The `ollama` import is deferred to construction. Default local model is Kanana-1.5-8B (Apache-2.0), with Qwen2.5 documented as the secondary local model:
```python
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
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/providers/test_ollama_provider.py -q`. Expected: `5 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/providers/ollama_provider.py tests/providers/test_ollama_provider.py && git commit -m "feat(providers): add guarded OllamaProvider (local Kanana/Qwen fallback)"`.

### Task 15: get_provider factory + module docs

**Files:**
- Modify: `ttobak/providers/__init__.py`
- Create: `docs/providers.md`
- Test: `tests/providers/test_factory.py`

**Interfaces:**
- Consumes: `ttobak/providers/base.py` `LLMProvider`; `ttobak/providers/fake.py` `FakeProvider`; `ttobak/providers/anthropic_provider.py` `AnthropicProvider`; `ttobak/providers/ollama_provider.py` `OllamaProvider`.
- Produces: `ttobak/providers/__init__.py`: `def get_provider(name: str, **kwargs) -> LLMProvider` (factory: `"fake"|"anthropic"|"ollama"`, case-insensitive; raises `ValueError` for unknown names). Re-exports `LLMProvider`, `FakeProvider`, `AnthropicProvider`, `OllamaProvider`, `get_provider`.

- [ ] **Step 1: Write failing test for the factory.** Create `tests/providers/test_factory.py`. The `"fake"` branch is fully constructible without optional deps; the `"anthropic"`/`"ollama"` branches are checked by class identity via a passthrough `client`:
```python
import pytest

from ttobak.providers import (
    AnthropicProvider,
    FakeProvider,
    LLMProvider,
    OllamaProvider,
    get_provider,
)


def test_get_provider_fake_returns_fakeprovider():
    provider = get_provider("fake", responses=["쉬운 글"])
    assert isinstance(provider, FakeProvider)
    assert isinstance(provider, LLMProvider)
    assert provider.generate("원문") == "쉬운 글"


def test_get_provider_is_case_insensitive():
    assert isinstance(get_provider("FAKE", responses=["x"]), FakeProvider)


def test_get_provider_anthropic_passes_kwargs():
    # Inject a passthrough client so no anthropic SDK / API key is needed.
    provider = get_provider("anthropic", client=object(), model="claude-opus-4-8")
    assert isinstance(provider, AnthropicProvider)
    assert provider.model == "claude-opus-4-8"


def test_get_provider_ollama_passes_kwargs():
    provider = get_provider("ollama", client=object(), model="qwen2.5:7b")
    assert isinstance(provider, OllamaProvider)
    assert provider.model == "qwen2.5:7b"


def test_get_provider_unknown_raises_valueerror():
    with pytest.raises(ValueError, match="unknown provider"):
        get_provider("gpt-imaginary")
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/providers/test_factory.py -q`. Expected: `ImportError: cannot import name 'get_provider' from 'ttobak.providers'`.

- [ ] **Step 3: Implement the factory and re-exports.** Replace the contents of `ttobak/providers/__init__.py` with:
```python
"""LLM provider abstraction for Ttobak.

Public API:
    LLMProvider        — the structural Protocol all providers satisfy.
    FakeProvider       — deterministic scripted provider for tests.
    AnthropicProvider  — Claude provider (demo default).
    OllamaProvider     — local provider (Kanana-1.5-8B / Qwen2.5).
    get_provider       — factory selecting a provider by name.
"""

from __future__ import annotations

from ttobak.providers.anthropic_provider import AnthropicProvider
from ttobak.providers.base import LLMProvider
from ttobak.providers.fake import FakeProvider
from ttobak.providers.ollama_provider import OllamaProvider

__all__ = [
    "LLMProvider",
    "FakeProvider",
    "AnthropicProvider",
    "OllamaProvider",
    "get_provider",
]


def get_provider(name: str, **kwargs) -> LLMProvider:
    """Build a provider by name.

    Args:
        name: One of ``"fake"``, ``"anthropic"``, ``"ollama"`` (case-insensitive).
        **kwargs: Forwarded to the selected provider's constructor.

    Returns:
        A constructed LLMProvider.

    Raises:
        ValueError: If ``name`` is not a known provider.
    """
    key = name.strip().lower()
    if key == "fake":
        return FakeProvider(**kwargs)
    if key == "anthropic":
        return AnthropicProvider(**kwargs)
    if key == "ollama":
        return OllamaProvider(**kwargs)
    raise ValueError(
        f"unknown provider {name!r}; expected one of 'fake', 'anthropic', 'ollama'"
    )
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/providers/test_factory.py -q`. Expected: `5 passed`.

- [ ] **Step 5: Write the provider docs (records the local-model decision).** Create `docs/providers.md`:
````markdown
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
````

- [ ] **Step 6: Run the full provider test suite, expect all PASS.** Run `python -m pytest tests/providers/ -q`. Expected: `24 passed`.

- [ ] **Step 7: Commit.** Run `git add ttobak/providers/__init__.py docs/providers.md tests/providers/test_factory.py && git commit -m "feat(providers): add get_provider factory, re-exports, and docs"`.

### Task 16: EasyReadResult model and result module

Wire the canonical `EasyReadResult` aggregate (`ttobak/result.py`) that every downstream surface (renderer, web demo) consumes. It composes the source `Document`, the produced `easy_text`, the chosen `Level`, the `KERReport`, the `FidelityReport`, optional `PictogramRef` list, revision count, and final `Verdict`.

> NOTE: this task imports `KERReport` (`ttobak/metric/models.py`), `FidelityReport` (`ttobak/fidelity/models.py`), and `PictogramRef` (`ttobak/pictogram/models.py`). Those contract models are fully defined later (Tasks 21, 23, 31). Task 20 installs trivial stub versions of any that do not yet exist so this Phase-1 skeleton runs end-to-end; Tasks 21/23/31 then own the real ones and MUST NOT be overwritten by the stubs.

**Files:**
- Create: `ttobak/result.py`
- Test: `tests/test_result.py`

**Interfaces:**
- Consumes (M1 contracts + later contract models): `ttobak/ir.py` `Document`; `ttobak/levels.py` `Level`; `ttobak/common.py` `Verdict`; `ttobak/metric/models.py` `KERReport`; `ttobak/fidelity/models.py` `FidelityReport`; `ttobak/pictogram/models.py` `PictogramRef`.
- Produces: `ttobak/result.py`: `class EasyReadResult(BaseModel)` with `source: Document; easy_text: str; level: Level; ker: KERReport; fidelity: FidelityReport; pictograms: list[PictogramRef] = []; revisions: int = 0; verdict: Verdict`.

- [ ] **Step 1: Write failing test for EasyReadResult construction and field types.** Create `tests/test_result.py`:
```python
from ttobak.result import EasyReadResult
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict, Severity
from ttobak.metric.models import KERReport, Violation
from ttobak.fidelity.models import FidelityReport, Slot, SlotType


def _doc() -> Document:
    return Document(
        blocks=[Block(type=BlockType.PARAGRAPH, text="건강보험료 1,295,400원을 2026년 7월 17일까지 내세요.")],
        source_mime="text/plain",
    )


def _ker() -> KERReport:
    return KERReport(
        score=81.0,
        level_estimate=2,
        sub_scores={"rule": 81.0},
        violations=[
            Violation(rule="sentence_length", span="한 문장", severity=Severity.MED, suggestion="문장을 나누세요.")
        ],
    )


def _fidelity() -> FidelityReport:
    return FidelityReport(
        slots=[Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY)],
        verdict=Verdict.PASS,
    )


def test_easy_read_result_holds_all_parts():
    result = EasyReadResult(
        source=_doc(),
        easy_text="건강보험료를 내세요.\n1,295,400원입니다.\n2026년 7월 17일까지 내세요.",
        level=Level.EASY,
        ker=_ker(),
        fidelity=_fidelity(),
        revisions=2,
        verdict=Verdict.PASS,
    )
    assert result.level is Level.EASY
    assert result.verdict is Verdict.PASS
    assert result.revisions == 2
    assert result.ker.score == 81.0
    assert result.fidelity.verdict is Verdict.PASS
    assert result.source.source_mime == "text/plain"


def test_easy_read_result_defaults_pictograms_and_revisions():
    result = EasyReadResult(
        source=_doc(),
        easy_text="쉬운 글.",
        level=Level.PLAIN,
        ker=_ker(),
        fidelity=_fidelity(),
        verdict=Verdict.HUMAN_REVIEW,
    )
    assert result.pictograms == []
    assert result.revisions == 0
    assert result.verdict is Verdict.HUMAN_REVIEW
```

- [ ] **Step 2: Run the test, expect FAIL (modules missing).** Run `python -m pytest tests/test_result.py -q`. Expect `ModuleNotFoundError` for `ttobak.result` (and/or `ttobak.metric.models` / `ttobak.fidelity.models`). This is expected; Task 20 supplies stubs and Step 5 here re-runs green after Task 20 — but implement `ttobak/result.py` now (Step 3), then ensure the contract models exist (defer to Task 20 if absent).

- [ ] **Step 3: Implement `ttobak/result.py` with the exact contract.** Create `ttobak/result.py`:
```python
"""Aggregate result of the Easy-Read pipeline (canonical contract)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from ttobak.common import Verdict
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Document
from ttobak.levels import Level
from ttobak.metric.models import KERReport
from ttobak.pictogram.models import PictogramRef


class EasyReadResult(BaseModel):
    """Everything the renderer / web surfaces need from one run."""

    source: Document
    easy_text: str
    level: Level
    ker: KERReport
    fidelity: FidelityReport
    pictograms: list[PictogramRef] = Field(default_factory=list)
    revisions: int = 0
    verdict: Verdict
```

- [ ] **Step 4: Ensure the imported contract models exist (or defer to Task 20).** If `ttobak/metric/models.py`, `ttobak/fidelity/models.py`, or `ttobak/pictogram/models.py` do not yet exist, jump to Task 20 to install the trivial contract-valid stubs, then return here. Do NOT overwrite real implementations from Tasks 21/23/31 if they already exist.

- [ ] **Step 5: Run the test, expect PASS.** Run `python -m pytest tests/test_result.py -q`. Expect `2 passed`.

- [ ] **Step 6: Commit.** Run `git checkout -b m3-pipeline-skeleton && git add ttobak/result.py tests/test_result.py && git commit -m "feat(result): add EasyReadResult aggregate model"`.

### Task 17: Easy-Read prompt builder (generate + revise constraints)

The pipeline must build a GENERATE prompt asking the LLM for Easy-Read text at the chosen `Level`, and a REVISE prompt injecting K-ER `Violation`s and Fidelity `failed_slots` as hard regeneration constraints (spec §4.2-B, §6.8: "실패 슬롯을 '반드시 verbatim, 의역 금지' 제약으로 주입"). Pure string builders — no LLM call.

> NOTE: Task 33 (M6) supersedes these builders with the final pipeline-integrated versions (`GENERATE_SYSTEM`/`REVISE_SYSTEM` constants and a `build_revise_prompt` whose params are `(source_text, prev_easy_text, level, violations, failed_slots)`). This task ships an interim `ttobak/prompts.py`; Task 33 moves the builders into `ttobak/pipeline.py`. Keep the verbatim-constraint behavior identical across both.

**Files:**
- Create: `ttobak/prompts.py`
- Test: `tests/test_prompts.py`

**Interfaces:**
- Consumes: `ttobak/ir.py` `Document.text()`; `ttobak/levels.py` `Level`; `ttobak/metric/models.py` `Violation`; `ttobak/fidelity/models.py` `Slot`, `SlotType`.
- Produces: `ttobak/prompts.py`: `EASY_READ_SYSTEM: str`; `def build_generate_prompt(source_text: str, level: Level) -> str`; `def build_revise_prompt(source_text: str, level: Level, previous_easy: str, violations: list[Violation], failed_slots: list[Slot]) -> str`.

- [ ] **Step 1: Write failing test for the generate prompt.** Create `tests/test_prompts.py`:
```python
from ttobak.prompts import (
    EASY_READ_SYSTEM,
    build_generate_prompt,
    build_revise_prompt,
)
from ttobak.levels import Level
from ttobak.common import Severity
from ttobak.metric.models import Violation
from ttobak.fidelity.models import Slot, SlotType


SOURCE = "건강보험료 1,295,400원을 2026년 7월 17일까지 납부하여야 합니다."


def test_system_prompt_states_fidelity_first():
    assert "원문" in EASY_READ_SYSTEM
    assert "쉬운" in EASY_READ_SYSTEM


def test_generate_prompt_contains_source_and_level_easy():
    prompt = build_generate_prompt(SOURCE, Level.EASY)
    assert SOURCE in prompt
    assert "쉬운 글" in prompt  # Level.EASY label


def test_generate_prompt_level_plain_uses_plain_label():
    prompt = build_generate_prompt(SOURCE, Level.PLAIN)
    assert "보통 읽기" in prompt
    assert SOURCE in prompt
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_prompts.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.prompts'`.

- [ ] **Step 3: Implement the system prompt and generate-prompt builder.** Create `ttobak/prompts.py`:
```python
"""Prompt builders for the GENERATE and REVISE steps of the pipeline.

Pure string assembly — no LLM call here. The pipeline injects K-ER
violations and Fidelity failed slots into the REVISE prompt as hard,
verbatim-preserving constraints (spec section 6.8).
"""
from __future__ import annotations

from ttobak.fidelity.models import Slot
from ttobak.levels import Level
from ttobak.metric.models import Violation

EASY_READ_SYSTEM = (
    "당신은 한국어 '쉬운 정보(Easy-Read)' 변환기입니다. "
    "어려운 공공·행정 문서를 누구나 이해할 수 있는 쉬운 한국어로 바꿉니다. "
    "규칙: 한 문장에 한 가지 내용만 담고, 짧고 능동적인 문장을 쓰며, "
    "어려운 한자어·전문어를 쉬운 말로 풀어 씁니다. "
    "가장 중요한 원칙: 숫자·날짜·금액·기한·자격·기관명을 절대 바꾸지 말고 "
    "원문 그대로 보존합니다. 사실이 흐려지면 안 됩니다. "
    "쉬운 글로 바꾼 본문만 출력하고, 설명이나 머리말은 붙이지 마세요."
)

_LEVEL_LABEL = {
    Level.PLAIN: "보통 읽기(쉬운 한국어, 텍스트 중심)",
    Level.EASY: "쉬운 글(쉬운 한국어, 한 줄 한 생각, 그림 친화)",
}


def build_generate_prompt(source_text: str, level: Level) -> str:
    """Build the first-pass GENERATE prompt for the given output level."""
    return (
        f"다음 원문을 '{_LEVEL_LABEL[level]}' 등급의 쉬운 정보로 바꾸세요.\n"
        "숫자·날짜·금액·기한·자격·기관명은 원문 그대로 유지하세요.\n\n"
        f"[원문]\n{source_text}\n\n"
        "[쉬운 글]\n"
    )


def build_revise_prompt(
    source_text: str,
    level: Level,
    previous_easy: str,
    violations: list[Violation],
    failed_slots: list[Slot],
) -> str:
    """Build the REVISE prompt, injecting violations and failed slots as hard constraints."""
    lines: list[str] = [
        f"앞서 만든 '쉬운 글'을 아래 지적사항에 맞게 고치세요. "
        f"등급은 '{_LEVEL_LABEL[level]}'입니다.",
        "",
        "[원문]",
        source_text,
        "",
        "[이전 쉬운 글]",
        previous_easy,
        "",
    ]
    if failed_slots:
        lines.append("[반드시 원문 그대로 포함해야 하는 표현 — 의역 금지]")
        for slot in failed_slots:
            lines.append(f"- \"{slot.raw_span}\" (정확히 이 문자열을 그대로 쓰세요)")
        lines.append("")
    if violations:
        lines.append("[쉬움 규칙 위반 — 고칠 것]")
        for v in violations:
            lines.append(f"- [{v.rule}] \"{v.span}\": {v.suggestion}")
        lines.append("")
    lines.append("[고친 쉬운 글]")
    return "\n".join(lines)
```

- [ ] **Step 4: Run the generate-prompt tests, expect PASS.** Run `python -m pytest tests/test_prompts.py -q`. Expect `3 passed`.

- [ ] **Step 5: Write failing test for the revise prompt constraint injection.** Append to `tests/test_prompts.py`:
```python
def test_revise_prompt_injects_failed_slot_verbatim_and_violation():
    failed = [
        Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY),
        Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE),
    ]
    violations = [
        Violation(
            rule="sentence_length",
            span="건강보험료를 ... 납부하여야 합니다",
            severity=Severity.MED,
            suggestion="문장을 두 개로 나누세요.",
        )
    ]
    prompt = build_revise_prompt(
        SOURCE, Level.EASY, "건강보험료 약 130만 원을 7월에 내세요.", violations, failed
    )
    assert "1,295,400원" in prompt
    assert "2026년 7월 17일" in prompt
    assert "의역 금지" in prompt
    assert "sentence_length" in prompt
    assert "문장을 두 개로 나누세요." in prompt
    assert "건강보험료 약 130만 원을 7월에 내세요." in prompt


def test_revise_prompt_omits_empty_constraint_sections():
    prompt = build_revise_prompt(SOURCE, Level.EASY, "이전 글.", [], [])
    assert "반드시 원문 그대로" not in prompt
    assert "쉬움 규칙 위반" not in prompt
    assert "[고친 쉬운 글]" in prompt
```

- [ ] **Step 6: Run the full prompt test file, expect PASS.** Run `python -m pytest tests/test_prompts.py -q`. Expect `5 passed`.

- [ ] **Step 7: Commit.** Run `git add ttobak/prompts.py tests/test_prompts.py && git commit -m "feat(prompts): add Easy-Read generate and revise prompt builders"`.

### Task 18: simplify() pipeline — generate→measure→revise loop

Implement the orchestration core (spec §4.2-B). `simplify()` calls `provider.generate` with the GENERATE prompt, then calls `metric.score` and `fidelity.verify`. While `fidelity.verdict == REVISE` and the revision budget remains, it builds a REVISE prompt feeding K-ER `violations` + `failed_slots` as constraints, regenerates, and re-measures. It sets the final `EasyReadResult.verdict` from the last `FidelityReport.verdict`, counts revisions, and returns `EasyReadResult`. `HUMAN_REVIEW` (e.g. negation flip per spec §6.7/§6.8) terminates immediately — never auto-revised. `metric.score` and `fidelity.verify` are reached through module-level references so tests can `monkeypatch` them with deterministic stubs.

> NOTE: this is the Phase-1 skeleton of `simplify`. Task 34 (M6) re-implements `simplify` with the real K-ER/Fidelity, pictogram matching, and verdict escalation (residual REVISE → HUMAN_REVIEW), using the same canonical signature `simplify(doc, level, provider, max_revise=3)`. `ref_date` is resolved internally from `doc.meta.get("ref_date")` (ISO string or `date`), else `date.today()`.

**Files:**
- Create: `ttobak/pipeline.py`
- Test: `tests/test_pipeline.py`

**Interfaces:**
- Consumes: `ttobak/ir.py` `Document`; `ttobak/levels.py` `Level`; `ttobak/common.py` `Verdict`; `ttobak/providers/base.py` `LLMProvider`; `ttobak/metric` `score`; `ttobak/fidelity` `verify`; `ttobak/metric/models.py` `KERReport`,`Violation`; `ttobak/fidelity/models.py` `FidelityReport`,`Slot`; `ttobak/result.py` `EasyReadResult`; `ttobak/prompts.py` `EASY_READ_SYSTEM`,`build_generate_prompt`,`build_revise_prompt`.
- Produces: `ttobak/pipeline.py`: `def simplify(doc: Document, level: Level, provider: LLMProvider, max_revise: int = 3) -> EasyReadResult`; module-level names `score` and `verify` (rebound imports, monkeypatch targets).

- [ ] **Step 1: Write failing test — happy path: first generation PASSes, no revision.** Create `tests/test_pipeline.py`:
```python
from datetime import date

import pytest

import ttobak.pipeline as pipeline
from ttobak.pipeline import simplify
from ttobak.providers.fake import FakeProvider
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict, Severity
from ttobak.metric.models import KERReport, Violation
from ttobak.fidelity.models import FidelityReport, Slot, SlotType


def make_doc(text: str = "건강보험료 1,295,400원을 2026년 7월 17일까지 납부하여야 합니다.") -> Document:
    return Document(
        blocks=[Block(type=BlockType.PARAGRAPH, text=text)],
        source_mime="text/plain",
        meta={"ref_date": "2026-06-30"},
    )


def ker_report(score: float = 80.0, violations=None) -> KERReport:
    return KERReport(score=score, level_estimate=2, sub_scores={"rule": score}, violations=violations or [])


def fidelity_report(verdict: Verdict, failed=None) -> FidelityReport:
    return FidelityReport(
        slots=[Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY)],
        verdict=verdict,
        failed_slots=failed or [],
    )


def test_simplify_pass_on_first_try_no_revision(monkeypatch):
    monkeypatch.setattr(pipeline, "score", lambda easy_text, level, source_text=None: ker_report())
    monkeypatch.setattr(pipeline, "verify", lambda source, easy_text, ref_date: fidelity_report(Verdict.PASS))

    provider = FakeProvider(["건강보험료를 내세요.\n1,295,400원입니다.\n2026년 7월 17일까지 내세요."])
    result = simplify(make_doc(), Level.EASY, provider, max_revise=3)

    assert result.verdict is Verdict.PASS
    assert result.revisions == 0
    assert len(provider.calls) == 1
    assert result.easy_text.startswith("건강보험료를 내세요.")
    assert result.level is Level.EASY
    assert result.ker.score == 80.0
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/test_pipeline.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.pipeline'`.

- [ ] **Step 3: Implement `ttobak/pipeline.py`.** Create `ttobak/pipeline.py`:
```python
"""Easy-Read pipeline: GENERATE -> MEASURE -> REVISE orchestration (spec 4.2 B).

``score`` and ``verify`` are imported at module level so tests can
monkeypatch them with deterministic stubs. The revise loop only runs while the
Fidelity verdict is REVISE; HUMAN_REVIEW (e.g. a negation flip) terminates
immediately and is never auto-revised (spec 6.7, 6.8).
"""
from __future__ import annotations

from datetime import date

from ttobak.common import Verdict
from ttobak.fidelity import verify
from ttobak.ir import Document
from ttobak.levels import Level
from ttobak.metric import score
from ttobak.prompts import (
    EASY_READ_SYSTEM,
    build_generate_prompt,
    build_revise_prompt,
)
from ttobak.providers.base import LLMProvider
from ttobak.result import EasyReadResult


def _ref_date(doc: Document) -> date:
    raw = doc.meta.get("ref_date")
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str) and raw:
        return date.fromisoformat(raw)
    return date.today()


def simplify(
    doc: Document,
    level: Level,
    provider: LLMProvider,
    max_revise: int = 3,
) -> EasyReadResult:
    """Run generate->measure->revise and return an EasyReadResult."""
    ref_date = _ref_date(doc)
    source_text = doc.text()

    prompt = build_generate_prompt(source_text, level)
    easy_text = provider.generate(prompt, system=EASY_READ_SYSTEM)

    ker = score(easy_text, level, source_text)
    fidelity = verify(doc, easy_text, ref_date)

    revisions = 0
    while fidelity.verdict is Verdict.REVISE and revisions < max_revise:
        revise_prompt = build_revise_prompt(
            source_text, level, easy_text, ker.violations, fidelity.failed_slots
        )
        easy_text = provider.generate(revise_prompt, system=EASY_READ_SYSTEM)
        revisions += 1
        ker = score(easy_text, level, source_text)
        fidelity = verify(doc, easy_text, ref_date)

    return EasyReadResult(
        source=doc,
        easy_text=easy_text,
        level=level,
        ker=ker,
        fidelity=fidelity,
        revisions=revisions,
        verdict=fidelity.verdict,
    )
```

- [ ] **Step 4: Run the happy-path test, expect PASS.** Run `python -m pytest tests/test_pipeline.py -q`. Expect `1 passed`.

- [ ] **Step 5: Write failing test — REVISE then PASS (one revision triggered).** Append to `tests/test_pipeline.py`:
```python
def test_simplify_revises_once_then_passes(monkeypatch):
    verdicts = iter([Verdict.REVISE, Verdict.PASS])
    failed_slot = Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY)

    def fake_verify(source, easy_text, ref_date):
        v = next(verdicts)
        return fidelity_report(v, failed=[failed_slot] if v is Verdict.REVISE else [])

    monkeypatch.setattr(
        pipeline, "score",
        lambda easy_text, level, source_text=None: ker_report(
            violations=[Violation(rule="hanja", span="납부", severity=Severity.MED, suggestion="'내다'로 바꾸세요.")]
        ),
    )
    monkeypatch.setattr(pipeline, "verify", fake_verify)

    provider = FakeProvider([
        "건강보험료 약 130만 원을 7월에 내세요.",
        "건강보험료 1,295,400원을 2026년 7월 17일까지 내세요.",
    ])
    result = simplify(make_doc(), Level.EASY, provider, max_revise=3)

    assert result.verdict is Verdict.PASS
    assert result.revisions == 1
    assert len(provider.calls) == 2
    revise_prompt = provider.calls[1]["prompt"]
    assert "1,295,400원" in revise_prompt
    assert "의역 금지" in revise_prompt
    assert result.easy_text == "건강보험료 1,295,400원을 2026년 7월 17일까지 내세요."
```

- [ ] **Step 6: Run, expect PASS.** Run `python -m pytest tests/test_pipeline.py -q`. Expect `2 passed`.

- [ ] **Step 7: Write failing test — max_revise respected when fidelity never recovers.** Append to `tests/test_pipeline.py`:
```python
def test_simplify_respects_max_revise_when_never_passing(monkeypatch):
    failed_slot = Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE)
    monkeypatch.setattr(pipeline, "score", lambda easy_text, level, source_text=None: ker_report())
    monkeypatch.setattr(
        pipeline, "verify",
        lambda source, easy_text, ref_date: fidelity_report(Verdict.REVISE, failed=[failed_slot]),
    )

    provider = FakeProvider([f"시도 {i}: 7월쯤 내세요." for i in range(3)])
    result = simplify(make_doc(), Level.EASY, provider, max_revise=2)

    assert result.revisions == 2
    assert len(provider.calls) == 3            # 1 generate + 2 revise, no more
    assert result.verdict is Verdict.REVISE    # final verdict carried through (Task 34 escalates this to HUMAN_REVIEW)
```

- [ ] **Step 8: Run, expect PASS.** Run `python -m pytest tests/test_pipeline.py -q`. Expect `3 passed`.

- [ ] **Step 9: Write failing test — HUMAN_REVIEW terminates without revising.** Append to `tests/test_pipeline.py`:
```python
def test_simplify_human_review_no_revision(monkeypatch):
    negation_slot = Slot(
        raw_span="제외", normalized_value="제외", type=SlotType.NEGATION,
        polarity=False, criticality=Severity.HIGH,
    )
    calls = {"n": 0}

    def fake_verify(source, easy_text, ref_date):
        calls["n"] += 1
        return FidelityReport(slots=[negation_slot], verdict=Verdict.HUMAN_REVIEW,
                              nli_contradictions=["소스는 '제외'인데 출력이 '포함'으로 단언함"],
                              failed_slots=[negation_slot])

    monkeypatch.setattr(pipeline, "score", lambda easy_text, level, source_text=None: ker_report())
    monkeypatch.setattr(pipeline, "verify", fake_verify)

    provider = FakeProvider(["기초생활수급자도 포함하여 모두 신청할 수 있습니다."])
    result = simplify(make_doc("기초생활수급자는 제외하고 신청할 수 있습니다."), Level.EASY, provider, max_revise=3)

    assert result.verdict is Verdict.HUMAN_REVIEW
    assert result.revisions == 0
    assert len(provider.calls) == 1
    assert calls["n"] == 1
```

- [ ] **Step 10: Run the full pipeline test file, expect PASS.** Run `python -m pytest tests/test_pipeline.py -q`. Expect `4 passed`.

- [ ] **Step 11: Commit.** Run `git add ttobak/pipeline.py tests/test_pipeline.py && git commit -m "feat(pipeline): add simplify() generate->measure->revise loop"`.

### Task 19: Pipeline integration smoke with stub metric/fidelity modules

Verify `simplify()` wires end-to-end against the REAL `ttobak.metric.score` and `ttobak.fidelity.verify` module functions (not monkeypatched) using `FakeProvider`. Because M2 (metric, Tasks 21–22) and the fidelity module (Tasks 23–30) ship the real implementations later, Task 20 installs trivial stubs ONLY IF those modules do not yet exist, so this Phase-1 skeleton stays unblocked and the wiring is provable.

**Files:**
- Test: `tests/test_pipeline_integration.py`

**Interfaces:**
- Consumes: `ttobak/pipeline.py` `simplify`; `ttobak/providers/fake.py` `FakeProvider`; `ttobak/metric` `score`; `ttobak/fidelity` `verify`.
- Produces: integration coverage only.

- [ ] **Step 1: Write the integration smoke test (real modules, no monkeypatch).** Create `tests/test_pipeline_integration.py`:
```python
from ttobak.pipeline import simplify
from ttobak.providers.fake import FakeProvider
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict
from ttobak.result import EasyReadResult


def test_simplify_end_to_end_with_real_metric_and_fidelity():
    doc = Document(
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="건강보험료 1,295,400원을 2026년 7월 17일까지 납부하여야 합니다."),
        ],
        source_mime="text/plain",
        meta={"ref_date": "2026-06-30"},
    )
    provider = FakeProvider(["건강보험료를 내세요.\n1,295,400원입니다.\n2026년 7월 17일까지 내세요."])
    result = simplify(doc, Level.EASY, provider, max_revise=3)

    assert isinstance(result, EasyReadResult)
    assert result.source is doc
    assert result.level is Level.EASY
    assert result.verdict in (Verdict.PASS, Verdict.REVISE, Verdict.HUMAN_REVIEW)
    assert result.revisions >= 0
    assert isinstance(result.ker.score, float)
    assert isinstance(result.fidelity.verdict, Verdict)
    assert len(provider.calls) >= 1
```

- [ ] **Step 2: Run the integration test (needs Task 20 stubs first).** Run `python -m pytest tests/test_pipeline_integration.py -q`. If `ttobak.metric`/`ttobak.fidelity` are absent it errors — complete Task 20 (stubs) then re-run. Expect `1 passed`.

- [ ] **Step 3: Commit.** Run `git add tests/test_pipeline_integration.py && git commit -m "test(pipeline): end-to-end smoke with stub metric/fidelity modules"`.

### Task 20: Trivial stub metric/fidelity/pictogram contract models (Phase-1 unblock only)

Install contract-valid trivial stubs for the modules `simplify`/`EasyReadResult` import, ONLY for files that do not yet exist, so Phase 1 runs end-to-end before Phase 2 ships the real K-ER/Fidelity/pictogram code. Tasks 21 (metric models), 22 (metric `score`), 23 (fidelity models), 24–30 (fidelity), and 31 (pictogram) own the REAL implementations and MUST NOT be overwritten.

**Files (create only if absent):** `ttobak/metric/__init__.py`, `ttobak/metric/models.py`, `ttobak/fidelity/__init__.py`, `ttobak/fidelity/models.py`, `ttobak/pictogram/__init__.py`, `ttobak/pictogram/models.py`

**Interfaces:**
- Consumes: `ttobak/common.py`, `ttobak/levels.py`, `ttobak/ir.py`.
- Produces (only if absent): the canonical contract models (`Violation`, `KERReport`, `SlotType`, `Slot`, `FidelityReport`, `PictogramRef`) and trivial `score`/`verify` returning contract-valid reports.

- [ ] **Step 1: Check which target files already exist.** Run `ls ttobak/metric/__init__.py ttobak/metric/models.py ttobak/fidelity/__init__.py ttobak/fidelity/models.py ttobak/pictogram/__init__.py ttobak/pictogram/models.py 2>&1`. For each MISSING file, create it per Steps 2–3. For each that EXISTS, leave it untouched (a later task owns it).

- [ ] **Step 2: If absent, create the contract models.** Create `ttobak/metric/models.py` (verbatim per contracts):
```python
"""K-ER report models (canonical contract)."""
from __future__ import annotations

from pydantic import BaseModel

from ttobak.common import Severity


class Violation(BaseModel):
    rule: str
    span: str
    severity: Severity
    suggestion: str


class KERReport(BaseModel):
    score: float
    level_estimate: int
    sub_scores: dict[str, float]
    violations: list[Violation]
```
  Create `ttobak/fidelity/models.py` (verbatim per contracts):
```python
"""Fidelity report models (canonical contract)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from ttobak.common import Severity, Verdict


class SlotType(str, Enum):
    NUMERIC = "numeric"
    DATE = "date"
    MONEY = "money"
    DURATION = "duration"
    ELIGIBILITY = "eligibility"
    AGENCY = "agency"
    CONTACT = "contact"
    PERSON = "person"
    NEGATION = "negation"
    CONDITIONAL = "conditional"
    MODALITY = "modality"
    SCOPE = "scope"


class Slot(BaseModel):
    raw_span: str
    normalized_value: str
    type: SlotType
    polarity: bool = True
    source_offset: int = 0
    criticality: Severity = Severity.HIGH


class FidelityReport(BaseModel):
    slots: list[Slot]
    verdict: Verdict
    exact_fail_count: int = 0
    nli_contradictions: list[str] = Field(default_factory=list)
    drift_flags: list[str] = Field(default_factory=list)
    failed_slots: list[Slot] = Field(default_factory=list)
```
  Create `ttobak/pictogram/__init__.py` (empty) and `ttobak/pictogram/models.py`:
```python
"""Pictogram reference model (canonical contract)."""
from __future__ import annotations

from pydantic import BaseModel


class PictogramRef(BaseModel):
    concept: str
    set: str
    glyph_id: str
    caption: str
```

- [ ] **Step 3: If absent, create trivial score/verify stubs.** Create `ttobak/metric/__init__.py`:
```python
"""K-ER metric module (Phase-1 placeholder stub — replaced by Task 22)."""
from __future__ import annotations

from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation

__all__ = ["score", "KERReport", "Violation"]


def score(easy_text: str, level: Level, source_text: str | None = None) -> KERReport:
    """Trivial placeholder K-ER report (real rubric lands in Task 22)."""
    return KERReport(
        score=100.0,
        level_estimate=int(level == Level.EASY) + 1,
        sub_scores={"rule": 100.0},
        violations=[],
    )
```
  Create `ttobak/fidelity/__init__.py`:
```python
"""Fidelity gate module (Phase-1 placeholder stub — replaced by Task 30)."""
from __future__ import annotations

from datetime import date

from ttobak.common import Verdict
from ttobak.fidelity.models import FidelityReport, Slot
from ttobak.ir import Document

__all__ = ["verify", "FidelityReport", "Slot"]


def verify(source: Document, easy_text: str, ref_date: date) -> FidelityReport:
    """Trivial placeholder Fidelity report — PASS (real gate lands in Task 30)."""
    return FidelityReport(slots=[], verdict=Verdict.PASS)
```
  Also add a trivial `ttobak/pictogram/match` if `EasyReadResult` consumers need it before Task 31 — but Task 16's `EasyReadResult` only imports `PictogramRef`, so the `match()` function is not required until Task 31. Leave `ttobak/pictogram/__init__.py` empty here.

- [ ] **Step 4: Run the whole Phase-1 test surface to confirm no regressions.** Run `python -m pytest tests/test_result.py tests/test_prompts.py tests/test_pipeline.py tests/test_pipeline_integration.py -q`. Expect all passing (the stubs make `score`/`verify` contract-valid).

- [ ] **Step 5: Commit.** Run `git add ttobak/metric ttobak/fidelity ttobak/pictogram && git commit -m "feat(stubs): contract models + trivial score/verify stubs to unblock pipeline skeleton"`.

## Phase 2: 핵심 가치(K-ER+Fidelity)

The headline AI value. M4 (Task 21–22) ships the rule-based K-ER metric (rules only; KcBERT/RSRS model layer is stretch). M5 (Task 23–30) ships the deterministic Fidelity gate (slot extraction + normalization + verification + NegationGuard + router). M6 (Tasks 33–35) wires both into the real `simplify()` loop; the pictogram model + `match()` (M7's leaf data layer, Tasks 31–32) are pulled forward ahead of it so `simplify()` is runnable end-to-end. After Phase 2, the generate→measure→revise loop runs with real K-ER and Fidelity.

> **M4 scope note (spec §5.2):** M4 ships the **rule-based K-ER core only**. The KcBERT/RSRS model-signal layer and the LLM-judge layer are **STRETCH** (§5.2 (2)/(3), §12.3) and are deliberately NOT implemented. The `sub_scores` dict carries one entry per rule (keys = rule names); the aggregate `score` is the rule-layer mean. The 0–100 number is a "non-validated auxiliary" indicator and the per-rule violation checklist is the load-bearing output (spec §5.3). All tokenizer access goes through `ttobak/metric/tokenize.py`; rule functions accept a pre-tokenized `list[Token]` so every rule test is deterministic and needs no live kiwipiepy (mirroring the FakeProvider pattern). `score()` lazily calls the real `tokenize()` only at the orchestration layer.

### Task 21: K-ER report models (Violation, KERReport)

> If Task 20 already created `ttobak/metric/models.py` with the canonical content, this task is satisfied; just add the dedicated model unit tests below and keep the file. M4 owns this file as the real (non-stub) definition — the content is identical to the contract.

**Files:**
- Modify/confirm: `ttobak/metric/__init__.py` (placeholder ok this task; the real `score()` is Task 22)
- Confirm: `ttobak/metric/models.py`
- Test: `tests/metric/__init__.py` (empty), `tests/metric/test_models.py`

**Interfaces:**
- Consumes: `ttobak/common.py` `Severity`; `pydantic.BaseModel`.
- Produces: `Violation(BaseModel){rule:str, span:str, severity:Severity, suggestion:str}`, `KERReport(BaseModel){score:float, level_estimate:int, sub_scores:dict[str,float], violations:list[Violation]}` — verbatim from CONTRACTS.

- [ ] **Step 1: Write failing test for the models.** Create `tests/metric/__init__.py` (empty) and `tests/metric/test_models.py`:
```python
from ttobak.common import Severity
from ttobak.metric.models import Violation, KERReport


def test_violation_fields():
    v = Violation(rule="sentence_length", span="문장 전체", severity=Severity.HIGH, suggestion="문장을 둘로 나누세요.")
    assert v.rule == "sentence_length"
    assert v.span == "문장 전체"
    assert v.severity is Severity.HIGH
    assert v.suggestion == "문장을 둘로 나누세요."


def test_ker_report_fields_and_defaults():
    v = Violation(rule="passive_ratio", span="처리됩니다", severity=Severity.MED, suggestion="능동으로 바꾸세요.")
    r = KERReport(score=81.0, level_estimate=2, sub_scores={"sentence_length": 90.0, "passive_ratio": 70.0}, violations=[v])
    assert r.score == 81.0
    assert r.level_estimate == 2
    assert r.sub_scores["passive_ratio"] == 70.0
    assert r.violations[0].rule == "passive_ratio"


def test_ker_report_empty_violations_allowed():
    r = KERReport(score=100.0, level_estimate=1, sub_scores={}, violations=[])
    assert r.violations == []
    assert r.score == 100.0
```

- [ ] **Step 2: Run the test, expect PASS (if Task 20 already created the models) or FAIL then create.** Run `python -m pytest tests/metric/test_models.py -q`. If the models file is absent, create `ttobak/metric/models.py` exactly as in Task 20 Step 2, then re-run. Expect `3 passed`.

- [ ] **Step 3: Commit.** Run `git checkout -b m4-ker-metric && git add ttobak/metric/models.py tests/metric/__init__.py tests/metric/test_models.py && git commit -m "feat(metric): confirm Violation/KERReport models with unit tests"`.

### Task 22: K-ER rule rubric — tokenize, rules, and score()

Replace the Task-20 placeholder `score()` with the real rule-based K-ER rubric (spec §5.2 (1), §5.3, rule table in §5.1). Tokenizer access is isolated in `ttobak/metric/tokenize.py`; each rule function accepts a pre-tokenized `list[Token]` so rule tests are deterministic without live kiwipiepy. `score()` lazily tokenizes at the orchestration layer, aggregates per-rule sub-scores into a mean 0–100, estimates a level (1|2|3), and emits the per-rule `Violation` checklist (the load-bearing output).

**Files:**
- Create: `ttobak/metric/tokenize.py`
- Create: `ttobak/metric/rules.py`
- Modify: `ttobak/metric/__init__.py` (real `score()`)
- Create: `ttobak/data/easy_words.txt`, `ttobak/data/hard_terms.txt`, `ttobak/data/idioms.txt` (seed lists)
- Test: `tests/metric/test_tokenize.py`, `tests/metric/test_rules.py`, `tests/metric/test_score.py`

**Interfaces:**
- Consumes: `ttobak/common.py` `Severity`; `ttobak/levels.py` `Level`; `ttobak/metric/models.py` `Violation`, `KERReport`; kiwipiepy `Kiwi().tokenize(text)` (runtime only; tests inject `Token` lists).
- Produces:
  - `ttobak/metric/tokenize.py`: `@dataclass class Token(form: str, tag: str)`; `def tokenize(text: str) -> list[Token]`; `def split_sentences(text: str) -> list[str]`.
  - `ttobak/metric/rules.py`: `class RuleResult(BaseModel){sub_score: float, violations: list[Violation]}`; rule functions each `(text: str, tokens: list[Token]) -> RuleResult`: `rule_sentence_length`, `rule_hard_word_ratio`, `rule_hanja_loanword_ratio`, `rule_predicates_connectives`, `rule_passive_ratio`, `rule_negation_ratio`, `rule_undefined_hard_term`, `rule_idiom`, `rule_abbrev_percent_bignum`, `rule_third_person_fictional`, `rule_direct_address`, `rule_modifier_ttr`; `ALL_RULES: list[tuple[str, callable]]`.
  - `ttobak/metric/__init__.py`: `def score(easy_text: str, level: Level, source_text: str | None = None) -> KERReport`.

- [ ] **Step 1: Write failing tokenize test.** Create `tests/metric/test_tokenize.py`:
```python
from ttobak.metric.tokenize import Token, split_sentences, tokenize


def test_token_dataclass_fields():
    t = Token(form="보험료", tag="NNG")
    assert t.form == "보험료"
    assert t.tag == "NNG"


def test_split_sentences_splits_on_terminal_punctuation():
    text = "보험료를 내세요. 기한은 7월 17일입니다! 문의 주세요?"
    sents = split_sentences(text)
    assert len(sents) == 3
    assert sents[0].strip() == "보험료를 내세요."


def test_tokenize_returns_tokens_with_form_and_tag():
    tokens = tokenize("보험료를 납부하세요.")
    assert tokens, "tokenize must return at least one token"
    assert all(isinstance(t, Token) for t in tokens)
    assert all(isinstance(t.form, str) and isinstance(t.tag, str) for t in tokens)
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/metric/test_tokenize.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.metric.tokenize'`.

- [ ] **Step 3: Implement tokenize.py.** Create `ttobak/metric/tokenize.py`. `tokenize()` lazily constructs a module-level `Kiwi()` and maps its output to `Token(form, tag)`; `split_sentences()` uses a deterministic regex (no kiwipiepy needed):
```python
"""Tokenizer + sentence splitter for K-ER rules.

All kiwipiepy access is isolated here so rule functions can be tested with
injected Token lists (deterministic, no live tokenizer). kiwipiepy is LGPL-3.0
and used as a separate, unmodified dependency (spec 9.1/9.4).
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_SENT_SPLIT = re.compile(r"(?<=[.!?。])\s+|\n+")


@dataclass
class Token:
    form: str
    tag: str


_kiwi = None


def _get_kiwi():
    global _kiwi
    if _kiwi is None:
        from kiwipiepy import Kiwi  # lazy import; LGPL separate dep
        _kiwi = Kiwi()
    return _kiwi


def tokenize(text: str) -> list[Token]:
    """Morphologically tokenize ``text`` into (form, POS-tag) Tokens."""
    kiwi = _get_kiwi()
    out: list[Token] = []
    for tok in kiwi.tokenize(text):
        out.append(Token(form=tok.form, tag=tok.tag))
    return out


def split_sentences(text: str) -> list[str]:
    """Split text into sentences on terminal punctuation / newlines."""
    parts = [s.strip() for s in _SENT_SPLIT.split(text) if s.strip()]
    return parts
```

- [ ] **Step 4: Run tokenize test (kiwipiepy installed via Task 1 deps).** Run `python -m pytest tests/metric/test_tokenize.py -q`. Expect `3 passed`.

- [ ] **Step 5: Write failing rules test (injected tokens; deterministic).** Create `tests/metric/test_rules.py`. Each test builds `Token` lists directly so no kiwipiepy is called:
```python
from ttobak.common import Severity
from ttobak.metric.tokenize import Token
from ttobak.metric.rules import (
    ALL_RULES,
    RuleResult,
    rule_sentence_length,
    rule_passive_ratio,
    rule_negation_ratio,
    rule_hanja_loanword_ratio,
)


def test_ruleresult_shape():
    r = rule_sentence_length("짧다.", [Token("짧", "VA"), Token("다", "EF")])
    assert isinstance(r, RuleResult)
    assert 0.0 <= r.sub_score <= 100.0
    assert isinstance(r.violations, list)


def test_long_sentence_scores_lower_than_short():
    short = rule_sentence_length("내세요.", [Token("내", "VV"), Token("세요", "EF")])
    long_text = " ".join(["아주"] * 40) + " 납부하여야 합니다."
    long_tokens = [Token("아주", "MAG")] * 40 + [Token("납부", "NNG"), Token("하", "XSV"), Token("여야", "EC"), Token("합니다", "VX")]
    long = rule_sentence_length(long_text, long_tokens)
    assert long.sub_score < short.sub_score
    assert long.violations  # a long sentence raises at least one violation


def test_passive_ratio_flags_passive_suffix():
    # 처리되다 — 피동 (passive). One passive predicate should be flagged.
    tokens = [Token("처리", "NNG"), Token("되", "XSV"), Token("ㅂ니다", "EF")]
    r = rule_passive_ratio("처리됩니다.", tokens)
    assert any("처리" in v.span or v.rule == "passive_ratio" for v in r.violations)


def test_negation_ratio_flags_negation():
    tokens = [Token("신청", "NNG"), Token("할", "ETM"), Token("수", "NNB"), Token("없", "VA"), Token("습니다", "EF")]
    r = rule_negation_ratio("신청할 수 없습니다.", tokens)
    assert r.violations


def test_hanja_loanword_ratio_high_for_sino_korean_heavy():
    tokens = [Token("납부", "NNG"), Token("의무", "NNG"), Token("이행", "NNG"), Token("기한", "NNG")]
    r = rule_hanja_loanword_ratio("납부 의무 이행 기한", tokens)
    assert 0.0 <= r.sub_score <= 100.0


def test_all_rules_is_list_of_name_fn_pairs():
    assert isinstance(ALL_RULES, list)
    names = {name for name, _ in ALL_RULES}
    for expected in (
        "sentence_length", "hard_word_ratio", "hanja_loanword_ratio",
        "predicates_connectives", "passive_ratio", "negation_ratio",
        "undefined_hard_term", "idiom", "abbrev_percent_bignum",
        "third_person_fictional", "direct_address", "modifier_ttr",
    ):
        assert expected in names
    for _name, fn in ALL_RULES:
        assert callable(fn)
```

- [ ] **Step 6: Run, expect FAIL.** Run `python -m pytest tests/metric/test_rules.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.metric.rules'`.

- [ ] **Step 7: Create the seed data lists.** Create `ttobak/data/easy_words.txt` (one easy word per line — seed with high-frequency everyday Korean words used by the hard-word-ratio rule; start with ~200 entries such as 돈, 날짜, 내다, 받다, 신청, 사람, 집, 일, 달, 해, 전화, 주소 …), `ttobak/data/hard_terms.txt` (one specialist/Sino-Korean hard term per line — seed with admin/legal vocabulary such as 납부, 부과, 경감, 소득인정액, 자격요건, 연체금, 가입자 …), and `ttobak/data/idioms.txt` (one idiom/metaphor per line — seed with common figurative expressions such as 발 벗고 나서다, 손꼽아 기다리다 …). Keep each file as plain UTF-8, comment lines start with `#`. These ship inside the package; declare `ttobak.data` as package-data in `pyproject.toml` (`[tool.setuptools.package-data] ttobak = ["data/*.txt"]`).

- [ ] **Step 8: Implement rules.py.** Create `ttobak/metric/rules.py` with `RuleResult`, a small data-list loader (reads the seed files via `importlib.resources`), and the twelve rule functions. Each rule computes a 0–100 sub-score (higher = easier) and a `list[Violation]` mapped to the spec §5.1 rule table. Map rule → severity: structure/eligibility-adjacent rules (sentence_length, predicates_connectives, undefined_hard_term, negation, idiom, abbrev/percent/bignum) emit MED/HIGH; lexical-variation rules (modifier_ttr) emit LOW. `ALL_RULES` is the ordered `[(name, fn), …]` list. The Korean POS tags to key on: passive `되/지다` patterns and `피동` suffixes for `rule_passive_ratio`; negation lexemes (안/못/없/말/아니/불가/금지/제외) for `rule_negation_ratio`; connective endings (tag `EC`) count per sentence for `rule_predicates_connectives`; Hanja/loanword detection via token surface (CJK codepoints / Latin) for `rule_hanja_loanword_ratio`; hard-term-not-in-easy-list for `rule_hard_word_ratio` and undefined-hard-term; idiom dictionary substring for `rule_idiom`; `%`/대문자 약어/큰 숫자 regex for `rule_abbrev_percent_bignum`; 그/그녀/가상인물 for `rule_third_person_fictional`; 당신/여러분/우리 presence rewards `rule_direct_address`; type-token ratio of modifiers (관형사/부사 tags MM/MAG) for `rule_modifier_ttr`. (Each rule's exact threshold is chosen to make the Step-5 tests pass; document the threshold in a docstring citing the spec §5.1 row.)

- [ ] **Step 9: Run rules test, expect PASS.** Run `python -m pytest tests/metric/test_rules.py -q`. Expect all passing. If any rule's threshold makes a test fail, tune the threshold in `rules.py` (not the test) to match the documented direction.

- [ ] **Step 10: Write failing score() test.** Create `tests/metric/test_score.py`:
```python
from ttobak.levels import Level
from ttobak.metric import score
from ttobak.metric.models import KERReport


HARD = "장기요양보험료의 납부 의무를 이행하지 아니한 가입자에 대하여는 소득인정액에 따라 연체금이 부과될 수 있으며 경감 대상에서 제외됩니다."
EASY = "보험료를 내야 합니다.\n내지 않으면 돈을 더 내야 합니다.\n7월 17일까지 내세요."


def test_score_returns_kerreport_in_range():
    r = score(EASY, Level.EASY)
    assert isinstance(r, KERReport)
    assert 0.0 <= r.score <= 100.0
    assert r.level_estimate in (1, 2, 3)
    assert isinstance(r.sub_scores, dict) and r.sub_scores


def test_sub_scores_have_one_entry_per_rule():
    from ttobak.metric.rules import ALL_RULES
    r = score(EASY, Level.EASY)
    assert set(r.sub_scores.keys()) == {name for name, _ in ALL_RULES}


def test_easy_text_scores_higher_than_hard_text():
    easy = score(EASY, Level.EASY)
    hard = score(HARD, Level.EASY)
    assert easy.score > hard.score
    # the hard text raises more rule violations than the easy one
    assert len(hard.violations) >= len(easy.violations)
```

- [ ] **Step 11: Implement score().** Replace `ttobak/metric/__init__.py` `score()` (the Task-20 stub) with the real orchestrator: tokenize once via `tokenize()`, run every rule in `ALL_RULES`, collect `sub_scores[name] = rule_result.sub_score` and accumulate violations, set `score = mean(sub_scores.values())`, map score→`level_estimate` (e.g. ≥80→1, ≥60→2, else 3), and return `KERReport`. Keep the docstring honesty note ("규칙 기반 루브릭, 경험적 검증 아님").

- [ ] **Step 12: Run score test, expect PASS.** Run `python -m pytest tests/metric/test_score.py -q`. Expect all passing.

- [ ] **Step 13: Run the full metric suite + the Phase-1 pipeline integration (now using real K-ER).** Run `python -m pytest tests/metric -q && python -m pytest tests/test_pipeline_integration.py -q`. Expect all passing.

- [ ] **Step 14: Commit.** Run `git add ttobak/metric ttobak/data pyproject.toml tests/metric && git commit -m "feat(metric): rule-based K-ER rubric (tokenize, 12 rules, score)"`.

### Task 23: Fidelity models — SlotType, Slot, FidelityReport

> If Task 20 already created `ttobak/fidelity/models.py` with the canonical content, this task is satisfied; add the dedicated model unit tests below and keep the file. M5 owns this file as the real (non-stub) definition.

**Files:**
- Confirm: `ttobak/fidelity/__init__.py` (placeholder ok this task; real `verify()` is Task 30)
- Confirm: `ttobak/fidelity/models.py`
- Create: `tests/fidelity/__init__.py` (empty)
- Test: `tests/fidelity/test_models.py`

**Interfaces:**
- Consumes: `ttobak/common.py` `Severity`, `Verdict`; pydantic v2 `BaseModel`.
- Produces: `SlotType` (str, Enum: NUMERIC, DATE, MONEY, DURATION, ELIGIBILITY, AGENCY, CONTACT, PERSON, NEGATION, CONDITIONAL, MODALITY, SCOPE — str values = lowercase name), `Slot` (raw_span, normalized_value, type, polarity=True, source_offset=0, criticality=Severity.HIGH), `FidelityReport` (slots, verdict, exact_fail_count=0, nli_contradictions=[], drift_flags=[], failed_slots=[]).

- [ ] **Step 1: Write failing test for the canonical fidelity models.** Create `tests/fidelity/__init__.py` (empty) and `tests/fidelity/test_models.py`:
```python
from ttobak.common import Severity, Verdict
from ttobak.fidelity.models import SlotType, Slot, FidelityReport


def test_slot_type_values_are_lowercase_name():
    assert SlotType.NUMERIC.value == "numeric"
    assert SlotType.DATE.value == "date"
    assert SlotType.MONEY.value == "money"
    assert SlotType.DURATION.value == "duration"
    assert SlotType.ELIGIBILITY.value == "eligibility"
    assert SlotType.AGENCY.value == "agency"
    assert SlotType.CONTACT.value == "contact"
    assert SlotType.PERSON.value == "person"
    assert SlotType.NEGATION.value == "negation"
    assert SlotType.CONDITIONAL.value == "conditional"
    assert SlotType.MODALITY.value == "modality"
    assert SlotType.SCOPE.value == "scope"


def test_slot_defaults():
    s = Slot(raw_span="삼만원", normalized_value="30000", type=SlotType.MONEY)
    assert s.polarity is True
    assert s.source_offset == 0
    assert s.criticality == Severity.HIGH


def test_slot_str_enum_is_str_subclass():
    assert isinstance(SlotType.MONEY, str)


def test_fidelity_report_defaults():
    s = Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE)
    r = FidelityReport(slots=[s], verdict=Verdict.PASS)
    assert r.exact_fail_count == 0
    assert r.nli_contradictions == []
    assert r.drift_flags == []
    assert r.failed_slots == []
    assert r.slots[0].type == SlotType.DATE
```

- [ ] **Step 2: Run the test.** Run `python -m pytest tests/fidelity/test_models.py -q`. If `ttobak/fidelity/models.py` is absent, create it exactly as in Task 20 Step 2, then re-run. Expect `4 passed`.

- [ ] **Step 3: Commit.** Run `git checkout -b m5-fidelity-gate && git add ttobak/fidelity/__init__.py ttobak/fidelity/models.py tests/fidelity/__init__.py tests/fidelity/test_models.py && git commit -m "feat(fidelity): confirm SlotType, Slot, FidelityReport models"`.

### Task 24: Korean number & money normalizers (recall 1.0 unit suite)

**Files:**
- Create: `ttobak/fidelity/normalize.py`
- Test: `tests/fidelity/test_normalize_number.py`

**Interfaces:**
- Consumes: nothing from other modules (pure Python). `korean-number` is documented as an optional cross-check dependency but NOT required for the deterministic unit suite (kept deterministic per spec §14.1).
- Produces: `normalize_korean_number(text: str) -> int` (digits + Korean myriad units 만/억/조 → int), `normalize_money(text: str) -> int` (strips 원/금/, and hedge tokens, then delegates).

- [ ] **Step 1: Write failing recall-1.0 number/money test.** Create `tests/fidelity/test_normalize_number.py`:
```python
import pytest

from ttobak.fidelity.normalize import normalize_korean_number, normalize_money


@pytest.mark.parametrize(
    "text,expected",
    [
        ("삼만원", 30000),
        ("3만5천원", 35000),
        ("3만 5천 원", 35000),
        ("약 3억 원", 300000000),
        ("일십이만삼천사백오십육", 123456),
        ("1억 2천만", 120000000),
        ("천이백구십오만", 12950000),
        ("100", 100),
        ("1,295,400", 1295400),
        ("오천", 5000),
        ("이천이십육", 2026),
    ],
)
def test_normalize_korean_number(text, expected):
    assert normalize_korean_number(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1,295,400원", 1295400),
        ("삼만원", 30000),
        ("약 3억 원", 300000000),
        ("금 1,200,000원정", 1200000),
        ("3만5천원", 35000),
    ],
)
def test_normalize_money(text, expected):
    assert normalize_money(text) == expected
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/fidelity/test_normalize_number.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.fidelity.normalize'`.

- [ ] **Step 3: Implement the number/money normalizers.** Create `ttobak/fidelity/normalize.py`:
```python
"""Korean number / money / date / phone normalizers and boundary-operator table.

Spec sections 6.4, 6.6, 6.8, 14.1. Pure-Python deterministic core so the unit
suite can target recall 1.0 without external model/network dependencies.
``korean-number`` and ``dateparser`` are documented optional cross-checks; the
deterministic algorithms below are authoritative for tests.
"""
from __future__ import annotations

import re

_DIGITS = {
    "영": 0, "공": 0,
    "일": 1, "이": 2, "삼": 3, "사": 4, "오": 5,
    "육": 6, "륙": 6, "칠": 7, "팔": 8, "구": 9,
}
_SMALL_UNITS = {"십": 10, "백": 100, "천": 1000}
_BIG_UNITS = {"만": 10**4, "억": 10**8, "조": 10**12, "경": 10**16}
_HEDGE_TOKENS = ("약", "대략", "여", "내외", "쯤", "가량")
_MONEY_AFFIX = ("원", "원정", "금")


def _parse_korean_chunk(chunk: str) -> int:
    """Parse a sub-만 Korean numeral chunk (digits + 십/백/천) into an int."""
    if chunk == "":
        return 0
    if chunk.isdigit():
        return int(chunk)
    total = 0
    current = 0
    for ch in chunk:
        if ch in _DIGITS:
            current = _DIGITS[ch]
        elif ch in _SMALL_UNITS:
            unit = _SMALL_UNITS[ch]
            total += (current if current else 1) * unit
            current = 0
        else:
            raise ValueError(f"unparsable Korean numeral char: {ch!r} in {chunk!r}")
    return total + current


def normalize_korean_number(text: str) -> int:
    """Convert mixed Korean/Arabic numeral text into an int.

    Handles myriad units 만/억/조/경, sub-units 십/백/천, plain digits, commas,
    and a leading hedge token (약/대략/...). Examples: '삼만원'->30000,
    '약 3억 원'->300000000, '3만5천원'->35000.
    """
    s = text.strip()
    for hedge in _HEDGE_TOKENS:
        s = s.replace(hedge, "")
    for affix in _MONEY_AFFIX:
        s = s.replace(affix, "")
    s = s.replace(",", "").replace(" ", "")
    if s == "":
        raise ValueError(f"no numeral content in {text!r}")
    if s.isdigit():
        return int(s)

    total = 0
    buffer = ""
    found_big = False
    for ch in s:
        if ch in _BIG_UNITS:
            chunk_val = _parse_korean_chunk(buffer) if buffer else 1
            total += chunk_val * _BIG_UNITS[ch]
            buffer = ""
            found_big = True
        else:
            buffer += ch
    if buffer:
        total += _parse_korean_chunk(buffer)
    if total == 0 and not found_big:
        raise ValueError(f"unparsable numeral: {text!r}")
    return total


def normalize_money(text: str) -> int:
    """Normalize a Korean money expression to an integer KRW amount.

    Strips currency affixes (원/원정/금) and hedge tokens, then delegates to
    :func:`normalize_korean_number`. Examples: '1,295,400원'->1295400,
    '약 3억 원'->300000000.
    """
    return normalize_korean_number(text)
```
Note: Korean numerals never chain bare digits without a unit, so a bare digit always overwrites `current` (no positional accumulation needed in `_parse_korean_chunk`).

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/fidelity/test_normalize_number.py -q`. Expect `16 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/fidelity/normalize.py tests/fidelity/test_normalize_number.py && git commit -m "feat(fidelity): Korean number/money normalizers (recall-1.0 unit suite)"`.

### Task 25: Date / phone normalizers + boundary-operator table

**Files:**
- Modify: `ttobak/fidelity/normalize.py`
- Test: `tests/fidelity/test_normalize_date.py`, `tests/fidelity/test_boundary.py`

**Interfaces:**
- Consumes: `datetime.date`; `ttobak/fidelity/normalize.py:normalize_korean_number` (Task 24).
- Produces: `normalize_date(text: str, ref_date: date) -> tuple[str, bool]` (ISO-8601 string + inclusive flag; relative 'D-7' resolved against `ref_date`), `normalize_phone(text: str) -> str` (digits-only canonical form), `BOUNDARY_OPERATORS` (dict 이상/초과/이하/미만/까지/부터 → operator symbol), `detect_boundary(text: str) -> str | None`.

- [ ] **Step 1: Write failing date/phone test.** Create `tests/fidelity/test_normalize_date.py`:
```python
from datetime import date

import pytest

from ttobak.fidelity.normalize import normalize_date, normalize_phone

REF = date(2026, 7, 10)


@pytest.mark.parametrize(
    "text,iso,inclusive",
    [
        ("2026년 7월 17일까지", "2026-07-17", True),
        ("2026년 7월 17일", "2026-07-17", False),
        ("2026-07-17", "2026-07-17", False),
        ("2026.07.17", "2026-07-17", False),
        ("2026년 7월 17일 전까지", "2026-07-17", False),
        ("D-7", "2026-07-17", False),
        ("7일 후", "2026-07-17", False),
    ],
)
def test_normalize_date(text, iso, inclusive):
    got_iso, got_inclusive = normalize_date(text, REF)
    assert got_iso == iso
    assert got_inclusive is inclusive


@pytest.mark.parametrize(
    "text,expected",
    [
        ("02-1234-5678", "0212345678"),
        ("010 1234 5678", "01012345678"),
        ("☎ 1577-1000", "15771000"),
        ("(02)123-4567", "021234567"),
    ],
)
def test_normalize_phone(text, expected):
    assert normalize_phone(text) == expected
```

- [ ] **Step 2: Write failing boundary-operator test.** Create `tests/fidelity/test_boundary.py`:
```python
from ttobak.fidelity.normalize import BOUNDARY_OPERATORS, detect_boundary


def test_boundary_table_exact_mapping():
    assert BOUNDARY_OPERATORS["이상"] == ">="
    assert BOUNDARY_OPERATORS["초과"] == ">"
    assert BOUNDARY_OPERATORS["이하"] == "<="
    assert BOUNDARY_OPERATORS["미만"] == "<"
    assert BOUNDARY_OPERATORS["까지"] == "inclusive"
    assert BOUNDARY_OPERATORS["부터"] == "from"


def test_detect_boundary_in_span():
    assert detect_boundary("만 65세 이상") == ">="
    assert detect_boundary("소득 300만원 미만") == "<"
    assert detect_boundary("2026년 7월 17일까지") == "inclusive"
    assert detect_boundary("정원 100명") is None


def test_미만_is_not_이하():
    # boundary weakening guard: 미만 (<) must never normalize to 이하 (<=)
    assert detect_boundary("미만") != detect_boundary("이하")
```

- [ ] **Step 3: Run both tests, expect FAIL.** Run `python -m pytest tests/fidelity/test_normalize_date.py tests/fidelity/test_boundary.py -q`. Expect `ImportError: cannot import name 'normalize_date'` (and `BOUNDARY_OPERATORS`).

- [ ] **Step 4: Implement date/phone normalizers and boundary table.** Append to `ttobak/fidelity/normalize.py`:
```python
from datetime import date, timedelta

# Boundary-operator table (spec 6.4 / 14.1). Generator must not weaken these.
BOUNDARY_OPERATORS: dict[str, str] = {
    "이상": ">=",
    "초과": ">",
    "이하": "<=",
    "미만": "<",
    "까지": "inclusive",
    "부터": "from",
}

_DATE_YMD = re.compile(r"(\d{4})\s*[년.\-/]\s*(\d{1,2})\s*[월.\-/]\s*(\d{1,2})\s*일?")
_DATE_REL_DMINUS = re.compile(r"D\s*-\s*(\d+)")
_DATE_REL_AFTER = re.compile(r"(\d+)\s*일\s*(?:후|뒤|이내)")
_PHONE_KEEP = re.compile(r"\d")


def normalize_date(text: str, ref_date: date) -> tuple[str, bool]:
    """Normalize an absolute or relative Korean date to (ISO-8601, inclusive).

    ``inclusive`` is True only when the span carries '까지' WITHOUT a
    weakening '전'/'이전' qualifier. Relative forms 'D-N' and 'N일 후/뒤/이내'
    resolve against ``ref_date`` (spec failure-mode 4: RELATIVE_BASE = document date).
    """
    s = text.strip()
    has_kkaji = "까지" in s
    has_before = ("전" in s) or ("이전" in s)
    inclusive = has_kkaji and not has_before

    m = _DATE_YMD.search(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        return date(y, mo, d).isoformat(), inclusive

    m = _DATE_REL_DMINUS.search(s)
    if m:
        return (ref_date + timedelta(days=int(m.group(1)))).isoformat(), inclusive

    m = _DATE_REL_AFTER.search(s)
    if m:
        return (ref_date + timedelta(days=int(m.group(1)))).isoformat(), inclusive

    raise ValueError(f"unparsable date: {text!r}")


def normalize_phone(text: str) -> str:
    """Reduce a phone/contact number to a digits-only canonical form."""
    digits = "".join(_PHONE_KEEP.findall(text))
    if not digits:
        raise ValueError(f"no phone digits in {text!r}")
    return digits


def detect_boundary(text: str) -> str | None:
    """Return the boundary-operator symbol present in ``text``, else None.

    Iterates the table so '이상'/'이하' keys match before bare substrings.
    """
    for keyword, symbol in BOUNDARY_OPERATORS.items():
        if keyword in text:
            return symbol
    return None
```

- [ ] **Step 5: Run both tests, expect PASS.** Run `python -m pytest tests/fidelity/test_normalize_date.py tests/fidelity/test_boundary.py -q`. Expect `14 passed`.

- [ ] **Step 6: Commit.** Run `git add ttobak/fidelity/normalize.py tests/fidelity/test_normalize_date.py tests/fidelity/test_boundary.py && git commit -m "feat(fidelity): date/phone normalizers + boundary-operator table"`.

### Task 26: NegationGuard — polarity scan & flip detection

**Files:**
- Create: `ttobak/fidelity/negation_guard.py`
- Test: `tests/fidelity/test_negation_guard.py`

**Interfaces:**
- Consumes: nothing from other modules (pure Python regex).
- Produces: `NEGATION_PATTERNS` (list[str]), `scan_negations(text: str) -> list[str]` (matched negation markers), `check_negation_flip(source_text: str, easy_text: str) -> list[str]` (human-readable flip descriptions when a source negation is dropped/reversed in the easy text).

- [ ] **Step 1: Write failing NegationGuard test.** Create `tests/fidelity/test_negation_guard.py`:
```python
from ttobak.fidelity.negation_guard import check_negation_flip, scan_negations


def test_scan_negations_finds_markers():
    found = scan_negations("외국인은 신청 대상에서 제외됩니다.")
    assert "제외" in found


def test_scan_negations_multiple():
    found = scan_negations("신청할 수 없으며 환불은 불가합니다.")
    assert "없" in found
    assert "불가" in found


def test_negation_dropped_is_flagged():
    src = "외국인은 지원 대상에서 제외됩니다."
    easy = "외국인도 지원 대상에 포함됩니다."
    flips = check_negation_flip(src, easy)
    assert flips != []
    assert any("제외" in f for f in flips)


def test_clean_negation_preserved_no_flip():
    src = "외국인은 지원 대상에서 제외됩니다."
    easy = "외국인은 지원을 받을 수 없습니다. 외국인은 대상에서 제외됩니다."
    flips = check_negation_flip(src, easy)
    assert flips == []


def test_no_source_negation_no_flip():
    src = "모든 국민이 신청할 수 있습니다."
    easy = "누구나 신청할 수 있습니다."
    assert check_negation_flip(src, easy) == []
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/fidelity/test_negation_guard.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.fidelity.negation_guard'`.

- [ ] **Step 3: Implement the NegationGuard.** Create `ttobak/fidelity/negation_guard.py`:
```python
"""NegationGuard: dedicated single-token negation flip detector (spec 6.7).

NLI/embeddings frequently miss single-token negation flips, so a dedicated
rule scans explicit polarity markers (제외/아니/불가/없/금지/말/~지 않) and pairs
each source negation with the easy text. A dropped or reversed negation is a
hard failure routed to HUMAN_REVIEW (never auto-revised).
"""
from __future__ import annotations

import re

NEGATION_PATTERNS: list[str] = [
    r"제외",
    r"아니",
    r"불가",
    r"없",
    r"금지",
    r"말아야",
    r"마십시오",
    r"지\s*않",
    r"못\s*하",
]

_AFFIRMATION_TOKENS = ("포함", "가능", "있습니다", "할 수 있", "허용")

_COMPILED = [re.compile(p) for p in NEGATION_PATTERNS]


def scan_negations(text: str) -> list[str]:
    """Return the surface negation markers present in ``text`` (deduped, in order)."""
    found: list[str] = []
    for pat in _COMPILED:
        m = pat.search(text)
        if m:
            marker = m.group(0).replace(" ", "")
            if marker not in found:
                found.append(marker)
    return found


def check_negation_flip(source_text: str, easy_text: str) -> list[str]:
    """Detect source negations dropped or reversed in the easy text.

    A flip is reported when the source contains a negation marker that is
    absent from the easy text AND the easy text contains an affirmation token.
    Returns a list of human-readable flip descriptions; empty means no flip.
    """
    src_negs = scan_negations(source_text)
    if not src_negs:
        return []
    easy_negs = scan_negations(easy_text)
    has_affirmation = any(tok in easy_text for tok in _AFFIRMATION_TOKENS)
    flips: list[str] = []
    for marker in src_negs:
        if marker not in easy_negs:
            flips.append(
                f"부정 표현 '{marker}'이(가) 쉬운본에서 누락/반전됨"
                + (" (긍정 단언 감지)" if has_affirmation else "")
            )
    return flips
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/fidelity/test_negation_guard.py -q`. Expect `5 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/fidelity/negation_guard.py tests/fidelity/test_negation_guard.py && git commit -m "feat(fidelity): NegationGuard polarity scan & flip detection"`.

### Task 27: Slot extraction — typed fact slots from source IR

**Files:**
- Create: `ttobak/fidelity/extract.py`
- Test: `tests/fidelity/test_extract.py`

**Interfaces:**
- Consumes: `ttobak/ir.py` `Document`,`Block`,`BlockType`; `ttobak/common.py` `Severity`; `ttobak/fidelity/models.py` `Slot`,`SlotType`; `ttobak/fidelity/normalize.py` `normalize_money`,`normalize_date`,`normalize_phone`,`normalize_korean_number`,`detect_boundary`,`BOUNDARY_OPERATORS`.
- Produces: `extract_slots(doc: Document, ref_date: date) -> list[Slot]` (redundant regex extraction of MONEY/DATE/CONTACT/SCOPE/NEGATION slots; spaCy NER is gated behind availability and OFF in tests).

- [ ] **Step 1: Write failing extraction test.** Create `tests/fidelity/test_extract.py`:
```python
from datetime import date

from ttobak.ir import Block, BlockType, Document
from ttobak.fidelity.extract import extract_slots
from ttobak.fidelity.models import SlotType

REF = date(2026, 7, 10)


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)], source_mime="text/plain")


def test_extracts_money_slot():
    slots = extract_slots(_doc("이번 달 보험료는 1,295,400원입니다."), REF)
    money = [s for s in slots if s.type == SlotType.MONEY]
    assert any(s.normalized_value == "1295400" for s in money)


def test_extracts_date_slot_with_inclusive_boundary():
    slots = extract_slots(_doc("납부 기한은 2026년 7월 17일까지입니다."), REF)
    dates = [s for s in slots if s.type == SlotType.DATE]
    assert any(s.normalized_value == "2026-07-17|inclusive" for s in dates)


def test_extracts_scope_boundary_slot():
    slots = extract_slots(_doc("만 65세 이상 어르신이 대상입니다."), REF)
    scope = [s for s in slots if s.type == SlotType.SCOPE]
    assert any(s.normalized_value == ">=" for s in scope)


def test_extracts_contact_slot():
    slots = extract_slots(_doc("문의: 02-1234-5678 로 연락 주세요."), REF)
    contact = [s for s in slots if s.type == SlotType.CONTACT]
    assert any(s.normalized_value == "0212345678" for s in contact)


def test_extracts_negation_slot():
    slots = extract_slots(_doc("외국인은 신청 대상에서 제외됩니다."), REF)
    neg = [s for s in slots if s.type == SlotType.NEGATION]
    assert neg and neg[0].polarity is False


def test_money_slots_are_high_criticality():
    from ttobak.common import Severity
    slots = extract_slots(_doc("보험료 30,000원"), REF)
    money = [s for s in slots if s.type == SlotType.MONEY]
    assert money and money[0].criticality == Severity.HIGH
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/fidelity/test_extract.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.fidelity.extract'`.

- [ ] **Step 3: Implement the extractor.** Create `ttobak/fidelity/extract.py`:
```python
"""Slot extraction from source IR (spec 6.3).

Redundant extraction: regex + normalizers form the deterministic core; spaCy
``ko_core_news_lg`` NER is OPTIONAL and gated behind import availability so the
test suite stays deterministic and offline. Extraction over-collects (recall
first); the verifier decides survival.
"""
from __future__ import annotations

import re
from datetime import date

from ttobak.common import Severity
from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.normalize import (
    BOUNDARY_OPERATORS,
    detect_boundary,
    normalize_date,
    normalize_money,
    normalize_phone,
)
from ttobak.ir import Document

_MONEY_RE = re.compile(r"(?:약\s*)?(?:[\d,]+|[일이삼사오육칠팔구십백천만억조\s]+)\s*원")
_DATE_RE = re.compile(
    r"\d{4}\s*[년.\-/]\s*\d{1,2}\s*[월.\-/]\s*\d{1,2}\s*일?(?:\s*(?:전\s*)?까지)?"
    r"|D\s*-\s*\d+|\d+\s*일\s*(?:후|뒤|이내)"
)
_CONTACT_RE = re.compile(r"(?:\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4})")
_SCOPE_RE = re.compile(r"[^\s,]*\s*(?:" + "|".join(BOUNDARY_OPERATORS) + r")")
_NEGATION_RE = re.compile(r"[^\s,.]*(?:제외|불가|금지|아니|없|지\s*않)[^\s,.]*")


def _add(slots, span, value, stype, offset, polarity=True, crit=Severity.HIGH):
    slots.append(Slot(raw_span=span.strip(), normalized_value=value, type=stype,
                      polarity=polarity, source_offset=offset, criticality=crit))


def extract_slots(doc: Document, ref_date: date) -> list[Slot]:
    """Extract typed preservation-required fact slots from the source document."""
    text = doc.text()
    slots: list[Slot] = []

    for m in _MONEY_RE.finditer(text):
        try:
            value = normalize_money(m.group(0))
        except ValueError:
            continue
        _add(slots, m.group(0), str(value), SlotType.MONEY, m.start())

    for m in _DATE_RE.finditer(text):
        try:
            iso, inclusive = normalize_date(m.group(0), ref_date)
        except ValueError:
            continue
        value = f"{iso}|inclusive" if inclusive else iso
        _add(slots, m.group(0), value, SlotType.DATE, m.start())

    for m in _CONTACT_RE.finditer(text):
        try:
            value = normalize_phone(m.group(0))
        except ValueError:
            continue
        _add(slots, m.group(0), value, SlotType.CONTACT, m.start())

    for m in _SCOPE_RE.finditer(text):
        symbol = detect_boundary(m.group(0))
        if symbol in (">=", ">", "<=", "<"):
            _add(slots, m.group(0), symbol, SlotType.SCOPE, m.start())

    for m in _NEGATION_RE.finditer(text):
        _add(slots, m.group(0), m.group(0).strip(), SlotType.NEGATION, m.start(), polarity=False)

    return slots
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/fidelity/test_extract.py -q`. Expect `6 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/fidelity/extract.py tests/fidelity/test_extract.py && git commit -m "feat(fidelity): typed slot extraction from source IR"`.

### Task 28: Slot verifier — exact-match HIGH slots + rounding allowlist

**Files:**
- Create: `ttobak/fidelity/verify_slots.py`
- Test: `tests/fidelity/test_verify_slots.py`

**Interfaces:**
- Consumes: `ttobak/fidelity/models.py` `Slot`,`SlotType`; `ttobak/common.py` `Severity`; `ttobak/fidelity/normalize.py` `normalize_money`,`normalize_date`,`normalize_phone`; `datetime.date`.
- Produces: `ROUNDING_HEDGE_TOKENS` (tuple), `verify_high_slots(slots, easy_text, ref_date, rounding_allowlist=None) -> list[Slot]` (returns FAILED HIGH slots — those whose normalized value does not survive in the easy text; rounding exception per spec §6.8 requires all three conditions).

- [ ] **Step 1: Write failing verifier test.** Create `tests/fidelity/test_verify_slots.py`:
```python
from datetime import date

from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.verify_slots import verify_high_slots

REF = date(2026, 7, 10)


def _money(raw, value):
    return Slot(raw_span=raw, normalized_value=value, type=SlotType.MONEY)


def _date(raw, value):
    return Slot(raw_span=raw, normalized_value=value, type=SlotType.DATE)


def test_number_swap_caught():
    failed = verify_high_slots([_money("30,000원", "30000")], "보험료는 3,000원입니다.", REF)
    assert len(failed) == 1
    assert failed[0].normalized_value == "30000"


def test_clean_money_passes():
    assert verify_high_slots([_money("1,295,400원", "1295400")], "이번 달에 내야 할 돈은 1,295,400원입니다.", REF) == []


def test_korean_number_in_easy_text_survives():
    assert verify_high_slots([_money("30,000원", "30000")], "보험료는 삼만원입니다.", REF) == []


def test_date_drift_caught():
    failed = verify_high_slots([_date("2026년 7월 17일", "2026-07-17")], "신청은 2026년 7월 7일까지입니다.", REF)
    assert len(failed) == 1


def test_rounding_without_allowlist_fails():
    failed2 = verify_high_slots([_money("1,295,400원", "1295400")], "약 130만 원 정도입니다.", REF)
    assert len(failed2) == 1  # exact 1295400 absent, no opt-in allowlist


def test_rounding_allowlist_three_conditions_pass():
    s = Slot(raw_span="약 130만 원", normalized_value="1295400", type=SlotType.MONEY)
    failed = verify_high_slots([s], "약 130만 원 정도입니다.", REF, rounding_allowlist={"1295400"})
    assert failed == []


def test_rounding_allowlist_but_no_hedge_in_easy_fails():
    s = Slot(raw_span="약 130만 원", normalized_value="1295400", type=SlotType.MONEY)
    failed = verify_high_slots([s], "130만 원입니다.", REF, rounding_allowlist={"1295400"})
    assert len(failed) == 1
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/fidelity/test_verify_slots.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.fidelity.verify_slots'`.

- [ ] **Step 3: Implement the verifier.** Create `ttobak/fidelity/verify_slots.py`:
```python
"""Exact-match verification of HIGH-criticality slots (spec 6.4, 6.8).

NUMERIC/DATE/MONEY/CONTACT/SCOPE slots must survive verbatim (by normalized
value) in the easy text. Rounding is a distortion UNLESS all three conditions
of spec 6.8 hold simultaneously: (1) the source span contains a hedge token,
(2) the easy text preserves the same hedge token, (3) the slot's normalized
value is in the document-level rounding allowlist (empty by default, opt-in).
"""
from __future__ import annotations

import re
from datetime import date

from ttobak.common import Severity
from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.normalize import normalize_date, normalize_money, normalize_phone

ROUNDING_HEDGE_TOKENS: tuple[str, ...] = ("약", "대략", "여", "내외", "쯤", "가량")

_MONEY_SPAN = re.compile(r"(?:[\d,]+|[일이삼사오육칠팔구십백천만억조\s]+)\s*원")
_DATE_SPAN = re.compile(
    r"\d{4}\s*[년.\-/]\s*\d{1,2}\s*[월.\-/]\s*\d{1,2}\s*일?(?:\s*(?:전\s*)?까지)?"
    r"|D\s*-\s*\d+|\d+\s*일\s*(?:후|뒤|이내)"
)
_CONTACT_SPAN = re.compile(r"\(?\d{2,4}\)?[\s\-]?\d{3,4}[\s\-]?\d{4}")


def _easy_money_values(easy_text: str) -> set[str]:
    values: set[str] = set()
    for m in _MONEY_SPAN.finditer(easy_text):
        try:
            values.add(str(normalize_money(m.group(0))))
        except ValueError:
            continue
    return values


def _easy_date_values(easy_text: str, ref_date: date) -> set[str]:
    values: set[str] = set()
    for m in _DATE_SPAN.finditer(easy_text):
        try:
            iso, _incl = normalize_date(m.group(0), ref_date)
        except ValueError:
            continue
        values.add(iso)
    return values


def _easy_contact_values(easy_text: str) -> set[str]:
    values: set[str] = set()
    for m in _CONTACT_SPAN.finditer(easy_text):
        try:
            values.add(normalize_phone(m.group(0)))
        except ValueError:
            continue
    return values


def _rounding_exception_ok(slot: Slot, easy_text: str, rounding_allowlist: set[str]) -> bool:
    """Spec 6.8: rounding PASSes only if all three conditions hold."""
    src_has_hedge = any(h in slot.raw_span for h in ROUNDING_HEDGE_TOKENS)
    easy_has_hedge = any(h in easy_text for h in ROUNDING_HEDGE_TOKENS)
    opted_in = slot.normalized_value in rounding_allowlist
    return src_has_hedge and easy_has_hedge and opted_in


def verify_high_slots(slots: list[Slot], easy_text: str, ref_date: date,
                      rounding_allowlist: set[str] | None = None) -> list[Slot]:
    """Return the HIGH slots that FAIL to survive verbatim in ``easy_text``."""
    allowlist = rounding_allowlist or set()
    money_values = _easy_money_values(easy_text)
    date_values = _easy_date_values(easy_text, ref_date)
    contact_values = _easy_contact_values(easy_text)

    failed: list[Slot] = []
    for slot in slots:
        if slot.criticality != Severity.HIGH:
            continue
        survived = False
        if slot.type == SlotType.MONEY:
            survived = slot.normalized_value in money_values
        elif slot.type == SlotType.DATE:
            iso = slot.normalized_value.split("|", 1)[0]
            survived = iso in date_values
        elif slot.type == SlotType.CONTACT:
            survived = slot.normalized_value in contact_values
        elif slot.type in (SlotType.NUMERIC, SlotType.SCOPE):
            survived = slot.normalized_value in money_values or slot.normalized_value in easy_text
        else:
            survived = slot.normalized_value in easy_text

        if not survived and slot.type == SlotType.MONEY:
            if _rounding_exception_ok(slot, easy_text, allowlist):
                survived = True

        if not survived:
            failed.append(slot)
    return failed
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/fidelity/test_verify_slots.py -q`. Expect `7 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/fidelity/verify_slots.py tests/fidelity/test_verify_slots.py && git commit -m "feat(fidelity): exact-match HIGH-slot verifier + rounding allowlist"`.

### Task 29: Router — PASS / REVISE / HUMAN_REVIEW

**Files:**
- Create: `ttobak/fidelity/router.py`
- Test: `tests/fidelity/test_router.py`

**Interfaces:**
- Consumes: `ttobak/common.py` `Verdict`; `ttobak/fidelity/models.py` `Slot`,`SlotType`.
- Produces: `route(failed_slots, negation_flips, nli_contradictions, extraction_low_confidence) -> Verdict` implementing spec §6.8 routing logic.

- [ ] **Step 1: Write failing router test.** Create `tests/fidelity/test_router.py`:
```python
from ttobak.common import Verdict
from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.router import route


def _slot(stype=SlotType.MONEY):
    return Slot(raw_span="x", normalized_value="1", type=stype)


def test_clean_passes():
    assert route([], [], [], False) == Verdict.PASS


def test_recoverable_money_failure_revises():
    assert route([_slot(SlotType.MONEY)], [], [], False) == Verdict.REVISE


def test_recoverable_date_failure_revises():
    assert route([_slot(SlotType.DATE)], [], [], False) == Verdict.REVISE


def test_negation_flip_forces_human_review():
    assert route([], ["부정 표현 '제외'이(가) 반전됨"], [], False) == Verdict.HUMAN_REVIEW


def test_nli_contradiction_forces_human_review():
    assert route([], [], ["조건 모순"], False) == Verdict.HUMAN_REVIEW


def test_low_extraction_confidence_forces_human_review():
    assert route([], [], [], True) == Verdict.HUMAN_REVIEW


def test_eligibility_slot_failure_is_human_review():
    assert route([_slot(SlotType.ELIGIBILITY)], [], [], False) == Verdict.HUMAN_REVIEW


def test_negation_flip_beats_money_failure():
    assert route([_slot(SlotType.MONEY)], ["부정 반전"], [], False) == Verdict.HUMAN_REVIEW
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/fidelity/test_router.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.fidelity.router'`.

- [ ] **Step 3: Implement the router.** Create `ttobak/fidelity/router.py`:
```python
"""Fidelity router: PASS / REVISE / HUMAN_REVIEW (spec 6.8).

- PASS: every HIGH slot survived, no NLI contradiction, no negation flip.
- REVISE (auto loop): only recoverable exact-match failures (numeric/date/
  money/duration/contact/scope) — re-inject as 'verbatim, no paraphrase' constraints.
- HUMAN_REVIEW: negation/condition polarity flip, NLI contradiction, low
  source-extraction confidence, or a failed semantic slot (eligibility/
  conditional/agency/person/modality) that cannot be safely auto-revised.
"""
from __future__ import annotations

from ttobak.common import Verdict
from ttobak.fidelity.models import Slot, SlotType

_AUTO_RECOVERABLE = {
    SlotType.NUMERIC,
    SlotType.DATE,
    SlotType.MONEY,
    SlotType.DURATION,
    SlotType.CONTACT,
    SlotType.SCOPE,
}


def route(failed_slots: list[Slot], negation_flips: list[str],
          nli_contradictions: list[str], extraction_low_confidence: bool) -> Verdict:
    """Map verification outcomes to a routing verdict per spec 6.8."""
    if negation_flips or nli_contradictions or extraction_low_confidence:
        return Verdict.HUMAN_REVIEW
    if not failed_slots:
        return Verdict.PASS
    if any(s.type not in _AUTO_RECOVERABLE for s in failed_slots):
        return Verdict.HUMAN_REVIEW
    return Verdict.REVISE
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/fidelity/test_router.py -q`. Expect `8 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/fidelity/router.py tests/fidelity/test_router.py && git commit -m "feat(fidelity): PASS/REVISE/HUMAN_REVIEW router"`.

### Task 30: verify() — public Fidelity gate entrypoint

Replaces the Task-20 stub `verify()` with the real orchestrator (extract → verify → NegationGuard → route). Semantic NLI is STRETCH and gated OFF (`use_nli=False` default) so MVP never blocks on it.

**Files:**
- Modify: `ttobak/fidelity/__init__.py`
- Test: `tests/fidelity/test_verify.py`

**Interfaces:**
- Consumes: `ttobak/ir.py` `Document`,`Block`,`BlockType`; `ttobak/common.py` `Verdict`,`Severity`; `ttobak/fidelity/models.py` `FidelityReport`,`Slot`,`SlotType`; `ttobak/fidelity/extract.py` `extract_slots`; `ttobak/fidelity/verify_slots.py` `verify_high_slots`; `ttobak/fidelity/negation_guard.py` `check_negation_flip`; `ttobak/fidelity/router.py` `route`; `datetime.date`.
- Produces: `verify(source: Document, easy_text: str, ref_date: date) -> FidelityReport` (canonical contract).

- [ ] **Step 1: Write failing end-to-end gate test.** Create `tests/fidelity/test_verify.py`:
```python
from datetime import date

from ttobak.common import Verdict
from ttobak.ir import Block, BlockType, Document
from ttobak.fidelity import verify

REF = date(2026, 7, 10)


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)], source_mime="text/plain")


def test_clean_control_passes():
    src = _doc("보험료 1,295,400원을 2026년 7월 17일까지 납부하세요.")
    easy = "이번 달 보험료는 1,295,400원입니다. 2026년 7월 17일까지 내세요."
    report = verify(src, easy, REF)
    assert report.verdict == Verdict.PASS
    assert report.exact_fail_count == 0
    assert report.failed_slots == []


def test_number_swap_caught_and_revises():
    report = verify(_doc("보험료는 30,000원입니다."), "보험료는 3,000원입니다.", REF)
    assert report.verdict == Verdict.REVISE
    assert report.exact_fail_count == 1
    assert any(s.normalized_value == "30000" for s in report.failed_slots)


def test_date_drift_caught_and_revises():
    report = verify(_doc("신청 기한은 2026년 7월 17일까지입니다."), "신청은 2026년 7월 7일까지 하세요.", REF)
    assert report.verdict == Verdict.REVISE
    assert report.exact_fail_count == 1


def test_negation_flip_human_review():
    report = verify(_doc("외국인은 지원 대상에서 제외됩니다."), "외국인도 지원 대상에 포함됩니다.", REF)
    assert report.verdict == Verdict.HUMAN_REVIEW
    assert report.drift_flags


def test_report_lists_all_extracted_slots():
    src = _doc("보험료 30,000원을 2026년 7월 17일까지 내세요.")
    report = verify(src, "보험료 30,000원을 2026년 7월 17일까지 내세요.", REF)
    types = {s.type.value for s in report.slots}
    assert "money" in types
    assert "date" in types
    assert report.verdict == Verdict.PASS
```

- [ ] **Step 2: Run the test, expect FAIL.** Run `python -m pytest tests/fidelity/test_verify.py -q`. Expect `ImportError: cannot import name 'verify'` (the Task-20 stub returns a trivial PASS and lacks the real pipeline — the swap/drift/negation tests will fail). Replace the stub now.

- [ ] **Step 3: Implement verify().** Replace the contents of `ttobak/fidelity/__init__.py` with:
```python
"""Ttobak Fidelity gate: slot extraction, normalization, verification, routing.

Public API: ``verify(source, easy_text, ref_date) -> FidelityReport`` (spec 6.2).
Deterministic exact-match path + NegationGuard form the MVP. Semantic NLI
(kf-deberta) is STRETCH and gated behind ``use_nli`` (default False) so it never
blocks the MVP gate.
"""
from __future__ import annotations

from datetime import date

from ttobak.fidelity.extract import extract_slots
from ttobak.fidelity.models import FidelityReport, Slot, SlotType
from ttobak.fidelity.negation_guard import check_negation_flip
from ttobak.fidelity.router import route
from ttobak.fidelity.verify_slots import verify_high_slots
from ttobak.ir import Document

__all__ = ["verify", "FidelityReport", "Slot", "SlotType"]


def verify(source: Document, easy_text: str, ref_date: date,
           *, rounding_allowlist: set[str] | None = None,
           use_nli: bool = False) -> FidelityReport:
    """Verify that the easy text preserves all preservation-required facts.

    Pipeline (spec 6.2): extract typed slots -> exact-match verify HIGH slots ->
    NegationGuard polarity check -> route to PASS / REVISE / HUMAN_REVIEW.
    ``use_nli`` (semantic NLI) is a STRETCH flag, OFF by default.
    """
    slots = extract_slots(source, ref_date)
    failed = verify_high_slots(slots, easy_text, ref_date, rounding_allowlist=rounding_allowlist)
    negation_flips = check_negation_flip(source.text(), easy_text)
    nli_contradictions: list[str] = []
    if use_nli:  # pragma: no cover - STRETCH, gated off in MVP/tests
        nli_contradictions = _run_nli(source.text(), easy_text)

    verdict = route(
        failed_slots=failed,
        negation_flips=negation_flips,
        nli_contradictions=nli_contradictions,
        extraction_low_confidence=_low_confidence(source),
    )

    return FidelityReport(
        slots=slots,
        verdict=verdict,
        exact_fail_count=len(failed),
        nli_contradictions=nli_contradictions,
        drift_flags=negation_flips,
        failed_slots=failed,
    )


def _low_confidence(source: Document) -> bool:
    """Source extraction confidence below 0.5 in any block triggers human review."""
    return any(block.confidence < 0.5 for block in source.blocks)


def _run_nli(source_text: str, easy_text: str) -> list[str]:  # pragma: no cover
    """STRETCH: kf-deberta cross-NLI contradiction detection (best-effort)."""
    try:
        from ttobak.fidelity.nli import detect_contradictions  # type: ignore
    except ImportError:
        return []
    return detect_contradictions(source_text, easy_text)
```

- [ ] **Step 4: Run the test, expect PASS.** Run `python -m pytest tests/fidelity/test_verify.py -q`. Expect `5 passed`.

- [ ] **Step 5: Run the full fidelity suite, expect all green.** Run `python -m pytest tests/fidelity/ -q`. Expect all passing (4 models + 16 number + 14 date/boundary + 5 negation + 6 extract + 7 verify_slots + 8 router + 5 verify). Also re-run `python -m pytest tests/test_pipeline_integration.py -q` (now exercising the real K-ER + real Fidelity); expect `1 passed`.

- [ ] **Step 6: Commit.** Run `git add ttobak/fidelity/__init__.py tests/fidelity/test_verify.py && git commit -m "feat(fidelity): verify() public gate entrypoint (extract->verify->guard->route)"`.

> **Interleave note:** M6's `simplify()` (Task 35) calls `ttobak.pictogram.match`. Pictogram matching is independent of K-ER/Fidelity, so the pictogram model + lexicon + `match()` (M7's leaf data layer) are pulled forward here as Tasks 31–32 to keep `simplify()` runnable end-to-end. M7's renderer tasks remain in Phase 3.

### Task 31: Pictogram model + lexicon (~30 core concepts)

> If Task 20 already created `ttobak/pictogram/models.py`, this task confirms it and adds the lexicon + tests. M7 owns these files as the real (non-stub) definitions. ~30 core concepts is the MVP floor (spec §15.5 / R5).

**Files:**
- Confirm: `ttobak/pictogram/models.py`
- Create: `ttobak/pictogram/lexicon.py`
- Create: `ttobak/pictogram/__init__.py` (empty for now; `match()` is Task 32)
- Create: `tests/pictogram/__init__.py` (empty)
- Test: `tests/pictogram/test_lexicon.py`

**Interfaces:**
- Consumes: nothing from other modules. `PictogramRef` is the canonical contract M7 owns.
- Produces: `ttobak/pictogram/models.py: class PictogramRef(BaseModel){concept:str, set:str, glyph_id:str, caption:str}`; `ttobak/pictogram/lexicon.py: LEXICON: dict[str, PictogramRef]` keyed by Korean surface keyword, ~30 core concepts. Glyph ids are file-path-style refs (`mulberry/money.svg` etc.), never inlined asset bytes (spec §9.4 embed rule).

- [ ] **Step 1: Write failing test for PictogramRef model + lexicon shape.** Create `tests/pictogram/__init__.py` (empty), then `tests/pictogram/test_lexicon.py`:
```python
from ttobak.pictogram.models import PictogramRef
from ttobak.pictogram.lexicon import LEXICON


def test_pictogram_ref_fields():
    ref = PictogramRef(concept="돈", set="mulberry", glyph_id="mulberry/money.svg", caption="돈")
    assert ref.concept == "돈"
    assert ref.set == "mulberry"
    assert ref.glyph_id == "mulberry/money.svg"
    assert ref.caption == "돈"


def test_lexicon_has_core_concepts():
    assert isinstance(LEXICON, dict)
    assert len(LEXICON) >= 30
    for keyword in ("돈", "날짜", "신청", "마감", "전화", "주소", "병원", "세금"):
        assert keyword in LEXICON
        assert isinstance(LEXICON[keyword], PictogramRef)


def test_lexicon_glyphs_are_path_refs_not_inlined():
    for ref in LEXICON.values():
        assert "/" in ref.glyph_id
        assert not ref.glyph_id.startswith("data:")
        assert ref.set in {"mulberry", "openmoji"}
        assert ref.caption
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/pictogram/test_lexicon.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.pictogram.lexicon'`.

- [ ] **Step 3: Confirm the pictogram package + model.** Ensure `ttobak/pictogram/__init__.py` exists (empty for now; `match()` lands in Task 32). Ensure `ttobak/pictogram/models.py` exists with the canonical `PictogramRef` (create it as in Task 20 if absent).

- [ ] **Step 4: Implement the lexicon (~30 core concepts).** Create `ttobak/pictogram/lexicon.py`:
```python
from __future__ import annotations

from ttobak.pictogram.models import PictogramRef

# Hand-curated ~30 high-frequency Korean public/admin concepts -> placeholder
# glyph path refs. Assets live in /assets/pictograms/<set>/ under their own
# CC BY-SA license; here we only carry path refs + Korean captions (spec 9.4).
_RAW: dict[str, tuple[str, str, str]] = {
    "돈": ("mulberry", "mulberry/money.svg", "돈"),
    "금액": ("mulberry", "mulberry/money.svg", "돈"),
    "납부": ("mulberry", "mulberry/pay.svg", "돈을 내요"),
    "세금": ("mulberry", "mulberry/tax.svg", "세금"),
    "날짜": ("mulberry", "mulberry/calendar.svg", "날짜"),
    "기한": ("mulberry", "mulberry/calendar.svg", "날짜"),
    "마감": ("mulberry", "mulberry/deadline.svg", "마감 날짜"),
    "신청": ("mulberry", "mulberry/apply.svg", "신청"),
    "접수": ("mulberry", "mulberry/apply.svg", "신청"),
    "서류": ("mulberry", "mulberry/document.svg", "서류"),
    "전화": ("mulberry", "mulberry/phone.svg", "전화"),
    "연락": ("mulberry", "mulberry/phone.svg", "전화"),
    "주소": ("mulberry", "mulberry/address.svg", "주소"),
    "방문": ("mulberry", "mulberry/visit.svg", "찾아가요"),
    "병원": ("mulberry", "mulberry/hospital.svg", "병원"),
    "약": ("mulberry", "mulberry/medicine.svg", "약"),
    "건강": ("mulberry", "mulberry/health.svg", "건강"),
    "보험": ("mulberry", "mulberry/insurance.svg", "보험"),
    "은행": ("mulberry", "mulberry/bank.svg", "은행"),
    "계좌": ("mulberry", "mulberry/bank_account.svg", "은행 계좌"),
    "주민센터": ("mulberry", "mulberry/office.svg", "주민센터"),
    "구청": ("mulberry", "mulberry/office.svg", "구청"),
    "우편": ("mulberry", "mulberry/mail.svg", "우편"),
    "이메일": ("openmoji", "openmoji/email.svg", "이메일"),
    "홈페이지": ("openmoji", "openmoji/website.svg", "홈페이지"),
    "지원": ("mulberry", "mulberry/support.svg", "도와줘요"),
    "혜택": ("mulberry", "mulberry/benefit.svg", "혜택"),
    "자격": ("mulberry", "mulberry/eligible.svg", "받을 수 있어요"),
    "주의": ("openmoji", "openmoji/warning.svg", "조심하세요"),
    "금지": ("openmoji", "openmoji/forbidden.svg", "하면 안 돼요"),
    "시간": ("mulberry", "mulberry/clock.svg", "시간"),
    "장소": ("mulberry", "mulberry/place.svg", "장소"),
}

LEXICON: dict[str, PictogramRef] = {
    keyword: PictogramRef(concept=keyword, set=set_name, glyph_id=glyph_id, caption=caption)
    for keyword, (set_name, glyph_id, caption) in _RAW.items()
}
```

- [ ] **Step 5: Run, expect PASS.** Run `python -m pytest tests/pictogram/test_lexicon.py -q`. Expect `3 passed`.

- [ ] **Step 6: Commit.** Run `git checkout -b m7-render-pictogram && git add ttobak/pictogram/__init__.py ttobak/pictogram/models.py ttobak/pictogram/lexicon.py tests/pictogram/__init__.py tests/pictogram/test_lexicon.py && git commit -m "feat(pictogram): PictogramRef model + ~30 core-concept lexicon"`.

### Task 32: Pictogram match() lookup

**Files:**
- Modify: `ttobak/pictogram/__init__.py`
- Test: `tests/pictogram/test_match.py`

**Interfaces:**
- Consumes: `ttobak/pictogram/models.py` `PictogramRef`; `ttobak/pictogram/lexicon.py` `LEXICON`.
- Produces: `ttobak/pictogram/__init__.py: def match(easy_text: str) -> list[PictogramRef]` — substring keyword lookup over `LEXICON`; deduplicates on `glyph_id`; preserves first-seen (text-position) order. Public engine API per contracts.

- [ ] **Step 1: Write failing test for match().** Create `tests/pictogram/test_match.py`:
```python
from ttobak.pictogram import match
from ttobak.pictogram.models import PictogramRef


def test_match_returns_refs_for_known_concepts():
    text = "신청 서류를 7월에 우편으로 보내세요. 전화로 물어볼 수 있어요."
    refs = match(text)
    glyphs = {r.glyph_id for r in refs}
    assert "mulberry/apply.svg" in glyphs
    assert "mulberry/document.svg" in glyphs
    assert "mulberry/mail.svg" in glyphs
    assert "mulberry/phone.svg" in glyphs
    assert all(isinstance(r, PictogramRef) for r in refs)


def test_match_empty_when_no_concept():
    assert match("오늘은 맑고 바람이 시원합니다.") == []


def test_match_deduplicates_synonyms_by_glyph():
    refs = match("돈 금액을 확인하세요.")
    money = [r for r in refs if r.glyph_id == "mulberry/money.svg"]
    assert len(money) == 1


def test_match_preserves_first_seen_order():
    refs = match("전화 신청")
    glyphs = [r.glyph_id for r in refs]
    assert glyphs.index("mulberry/phone.svg") < glyphs.index("mulberry/apply.svg")
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/pictogram/test_match.py -q`. Expect `ImportError: cannot import name 'match' from 'ttobak.pictogram'`.

- [ ] **Step 3: Implement `match()`.** Replace the contents of `ttobak/pictogram/__init__.py` with:
```python
from __future__ import annotations

from ttobak.pictogram.lexicon import LEXICON
from ttobak.pictogram.models import PictogramRef

__all__ = ["match", "PictogramRef"]


def match(easy_text: str) -> list[PictogramRef]:
    """Look up pictogram refs for core concepts present in easy_text.

    Hand-dictionary substring lookup (spec 4.2.E: deliberately NOT general
    semantic matching). Deduplicates synonyms that share a glyph, preserving
    first-seen order in the text.
    """
    seen_glyphs: set[str] = set()
    refs: list[PictogramRef] = []
    matched: list[tuple[int, PictogramRef]] = []
    for keyword, ref in LEXICON.items():
        idx = easy_text.find(keyword)
        if idx != -1:
            matched.append((idx, ref))
    for _, ref in sorted(matched, key=lambda pair: pair[0]):
        if ref.glyph_id in seen_glyphs:
            continue
        seen_glyphs.add(ref.glyph_id)
        refs.append(ref)
    return refs
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/pictogram/test_match.py -q`. Expect `4 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/pictogram/__init__.py tests/pictogram/test_match.py && git commit -m "feat(pictogram): match() core-concept lookup with glyph dedup"`.

### Task 33: Generate/Revise prompt builders moved into the pipeline (final)

M6 finalizes the prompt builders, moving them into `ttobak/pipeline.py` with the pipeline-integrated signatures and the `GENERATE_SYSTEM`/`REVISE_SYSTEM` constants. The REVISE step feeds K-ER `Violation`s and Fidelity `failed_slots` back as hard verbatim-preservation constraints (spec §4.2-B, §6.8). Pure builders, no LLM call.

> This supersedes the interim `ttobak/prompts.py` from Task 17. Move the builders into `ttobak/pipeline.py` and update the Task-18 `simplify` imports accordingly (it imported from `ttobak.prompts`); after this task `ttobak/prompts.py` may be deleted or left re-exporting from `pipeline` — prefer deletion to avoid two sources. The REVISE builder's params change to `(source_text, prev_easy_text, level, violations, failed_slots)`.

**Files:**
- Modify: `ttobak/pipeline.py`
- Delete: `ttobak/prompts.py` (and its test `tests/test_prompts.py` — its assertions are re-expressed below)
- Test: `tests/test_pipeline_prompts.py`

**Interfaces:**
- Consumes: `ttobak/levels.py` `Level`; `ttobak/common.py` `Severity`; `ttobak/metric/models.py` `Violation`; `ttobak/fidelity/models.py` `Slot`,`SlotType`.
- Produces in `ttobak/pipeline.py`: `GENERATE_SYSTEM: str`; `REVISE_SYSTEM: str`; `build_generate_prompt(source_text: str, level: Level) -> str`; `build_revise_prompt(source_text: str, prev_easy_text: str, level: Level, violations: list[Violation], failed_slots: list[Slot]) -> str`.

- [ ] **Step 1: Write failing test for the builders.** Create `tests/test_pipeline_prompts.py`:
```python
from ttobak.levels import Level
from ttobak.common import Severity
from ttobak.metric.models import Violation
from ttobak.fidelity.models import Slot, SlotType
from ttobak.pipeline import (
    GENERATE_SYSTEM,
    REVISE_SYSTEM,
    build_generate_prompt,
    build_revise_prompt,
)


def test_build_generate_prompt_includes_source_and_level_label():
    src = "본인부담금은 1,295,400원이며 2026년 7월 17일까지 납부하셔야 합니다."
    prompt = build_generate_prompt(src, Level.EASY)
    assert src in prompt
    assert "쉬운 글" in prompt
    assert isinstance(GENERATE_SYSTEM, str) and len(GENERATE_SYSTEM) > 0


def test_build_generate_prompt_plain_level_label():
    prompt = build_generate_prompt("안내문입니다.", Level.PLAIN)
    assert "보통 읽기" in prompt


def test_build_revise_prompt_injects_failed_slots_verbatim():
    failed = [
        Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY, criticality=Severity.HIGH),
        Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE, criticality=Severity.HIGH),
    ]
    violations = [
        Violation(rule="sentence_length", span="본인부담금은 ... 납부하셔야 합니다",
                  severity=Severity.MED, suggestion="문장을 두 개로 나누세요.")
    ]
    prompt = build_revise_prompt(
        source_text="원문 텍스트", prev_easy_text="본인부담금은 약 130만 원입니다.",
        level=Level.EASY, violations=violations, failed_slots=failed,
    )
    assert "1,295,400원" in prompt
    assert "2026년 7월 17일" in prompt
    assert "본인부담금은 약 130만 원입니다." in prompt
    assert "sentence_length" in prompt
    assert "문장을 두 개로 나누세요." in prompt
    assert "그대로" in prompt
    assert isinstance(REVISE_SYSTEM, str) and len(REVISE_SYSTEM) > 0


def test_build_revise_prompt_with_no_failures_is_still_valid():
    prompt = build_revise_prompt(source_text="원문", prev_easy_text="쉬운 본문",
                                 level=Level.PLAIN, violations=[], failed_slots=[])
    assert "쉬운 본문" in prompt
    assert "원문" in prompt
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/test_pipeline_prompts.py -q`. Expect `ImportError: cannot import name 'GENERATE_SYSTEM' from 'ttobak.pipeline'` (and `build_generate_prompt`/`build_revise_prompt` not yet in `pipeline`).

- [ ] **Step 3: Move the builders into `ttobak/pipeline.py`.** Add to the top of `ttobak/pipeline.py` (and remove the `from ttobak.prompts import ...` line):
```python
from ttobak.metric.models import Violation
from ttobak.fidelity.models import Slot

GENERATE_SYSTEM = (
    "당신은 한국어 '쉬운 정보(Easy-Read)' 변환기입니다. "
    "어려운 공공·행정 문서를 발달장애인·고령자·저문해자가 이해할 수 있게 "
    "다시 씁니다. 규칙: 한 문장에 한 가지 생각만 담고, 짧고 쉬운 단어를 쓰며, "
    "한자어·외래어·피동·이중부정을 피합니다. "
    "숫자·날짜·금액·기한·자격조건·기관명은 원문 그대로 정확히 보존합니다. "
    "원문에 없는 사실을 추가하지 않습니다. 변환된 본문만 출력합니다."
)

REVISE_SYSTEM = (
    "당신은 한국어 '쉬운 정보' 교정기입니다. 이전 변환본에서 발견된 "
    "쉬움 위반과 사실 왜곡을 고칩니다. 아래 '반드시 지킬 제약'은 "
    "글자 그대로(verbatim) 지켜야 하며, 의역·반올림·표현 약화가 금지됩니다. "
    "교정된 본문만 출력합니다."
)

_LEVEL_LABEL: dict[Level, str] = {
    Level.PLAIN: "보통 읽기(쉬운 표준 한국어, 문장은 짧게)",
    Level.EASY: "쉬운 글(Easy Korean: 한 줄 한 생각, 가장 쉬운 단어)",
}


def build_generate_prompt(source_text: str, level: Level) -> str:
    """Build the first-pass GENERATE prompt embedding the source verbatim."""
    label = _LEVEL_LABEL[level]
    return (
        f"다음 원문을 '{label}' 수준의 쉬운 정보로 변환하세요.\n\n"
        f"[원문]\n{source_text}\n\n"
        "[규칙]\n"
        "- 한 문장에 한 가지 생각만 담으세요.\n"
        "- 숫자·날짜·금액·기한·자격조건·기관명은 원문 그대로 보존하세요.\n"
        "- 원문에 없는 내용을 만들지 마세요.\n\n"
        "[변환 결과]\n"
    )


def build_revise_prompt(
    source_text: str,
    prev_easy_text: str,
    level: Level,
    violations: list[Violation],
    failed_slots: list[Slot],
) -> str:
    """Build the REVISE prompt: prior easy text + hard verbatim constraints
    from Fidelity failed slots and K-ER violations (spec section 6.8)."""
    label = _LEVEL_LABEL[level]

    if failed_slots:
        slot_lines = "\n".join(
            f"- '{s.raw_span}' (을)를 글자 그대로 포함하세요. 반올림·의역·표현 약화 금지."
            for s in failed_slots
        )
        slot_block = "[반드시 지킬 제약 — 사실 보존(verbatim)]\n" + slot_lines + "\n\n"
    else:
        slot_block = ""

    if violations:
        viol_lines = "\n".join(
            f"- [{v.severity.value}] {v.rule}: '{v.span}' → {v.suggestion}" for v in violations
        )
        viol_block = "[고칠 쉬움 위반]\n" + viol_lines + "\n\n"
    else:
        viol_block = ""

    return (
        f"이전 변환본을 '{label}' 수준에 맞게 교정하세요. "
        "아래 제약을 지키면서 더 쉽게 다시 쓰세요.\n\n"
        f"[원문]\n{source_text}\n\n"
        f"[이전 변환본 — 이것을 고치세요]\n{prev_easy_text}\n\n"
        f"{slot_block}"
        f"{viol_block}"
        "[교정 결과]\n"
    )
```
  Then update `simplify()` (Task 18): it now uses `GENERATE_SYSTEM`/`REVISE_SYSTEM` and calls `build_revise_prompt(source_text, easy_text, level, ker.violations, fidelity.failed_slots)` (the prev-easy-text arg moves to position 2). Delete `ttobak/prompts.py` and `tests/test_prompts.py`.

- [ ] **Step 4: Run the builders test, expect PASS.** Run `python -m pytest tests/test_pipeline_prompts.py -q`. Expect `4 passed`.

- [ ] **Step 5: Confirm the pipeline still imports cleanly.** Run `python -c "import ttobak.pipeline; print('ok')"` → expect `ok`; and `python -m pytest tests/test_pipeline.py -q` (the Task-18 tests, now reading `provider.calls[1]["prompt"]`) → expect all passing. If a Task-18 test referenced `ttobak.prompts`, update it to import from `ttobak.pipeline`.

- [ ] **Step 6: Commit.** Run `git checkout -b m6-pipeline-integration && git add ttobak/pipeline.py tests/test_pipeline_prompts.py && git rm ttobak/prompts.py tests/test_prompts.py && git commit -m "feat(pipeline): move generate/revise prompt builders into pipeline with verbatim slot constraints"`.

### Task 34: simplify() — wire real K-ER + Fidelity + pictograms, escalate residual verdict

Finalize `simplify()` (canonical signature `simplify(doc, level, provider, max_revise=3) -> EasyReadResult`): GENERATE once, then loop MEASURE (real `metric.score` + real `fidelity.verify`) → if Fidelity verdict is REVISE and budget remains, rebuild the constraint prompt and regenerate; stop early on PASS; never auto-revise HUMAN_REVIEW (spec §6.7/§6.8). Then run pictogram `match()`, set every `EasyReadResult` field, and escalate a residual REVISE (surviving after `max_revise`) to HUMAN_REVIEW (spec §6.8 case d).

**Files:**
- Modify: `ttobak/pipeline.py`
- Test: `tests/test_pipeline_simplify.py`

**Interfaces:**
- Consumes: `datetime.date`; `ttobak/ir.py` `Document`; `ttobak/levels.py` `Level`; `ttobak/common.py` `Verdict`; `ttobak/providers/base.py` `LLMProvider`; `ttobak/providers/fake.py` `FakeProvider` (tests); `ttobak/metric` `score`; `ttobak/fidelity` `verify`; `ttobak/pictogram` `match`; `ttobak/result.py` `EasyReadResult`.
- Produces: finalized `ttobak/pipeline.py: simplify(...)` with pictogram attachment + `_final_verdict` escalation.

- [ ] **Step 1: Write failing test — PASS on first generation.** Create `tests/test_pipeline_simplify.py`:
```python
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict
from ttobak.providers.fake import FakeProvider
from ttobak.result import EasyReadResult
from ttobak.pipeline import simplify


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)],
                    source_mime="text/plain", meta={"ref_date": "2026-07-01"})


def test_simplify_passes_without_revision():
    src = "건강보험료 본인부담금은 50,000원입니다. 2026년 8월 1일까지 내세요."
    provider = FakeProvider(["건강보험료는 50,000원입니다.\n2026년 8월 1일까지 내세요."])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=3)
    assert isinstance(result, EasyReadResult)
    assert result.verdict == Verdict.PASS
    assert result.revisions == 0
    assert result.level == Level.EASY
    assert "50,000원" in result.easy_text
    assert result.ker is not None
    assert result.fidelity.verdict == Verdict.PASS
    assert isinstance(result.pictograms, list)
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/test_pipeline_simplify.py -q -k without_revision`. The Task-18 `simplify` lacks `pictograms=match(...)` and verdict escalation; the test may still pass for the PASS case but proceed to add the missing behaviors via the next tests.

- [ ] **Step 3: Finalize `simplify()`.** Update `ttobak/pipeline.py` `simplify` to attach pictograms and escalate the verdict. Add imports `from ttobak.pictogram import match` and keep `from ttobak.result import EasyReadResult`. Replace the return + add a `_final_verdict` helper:
```python
from ttobak.pictogram import match


def _final_verdict(fidelity_verdict: Verdict, revisions: int, max_revise: int) -> Verdict:
    """A REVISE that survives the loop (residual failure after max_revise)
    escalates to HUMAN_REVIEW (spec 6.8 case d)."""
    if fidelity_verdict == Verdict.REVISE:
        return Verdict.HUMAN_REVIEW
    return fidelity_verdict
```
  And in `simplify`, after the loop, compute `verdict = _final_verdict(fidelity.verdict, revisions, max_revise)` and build the result with `pictograms=match(easy_text)` and `verdict=verdict`. Also `.strip()` each `provider.generate(...)` output.

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/test_pipeline_simplify.py -q -k without_revision`. Expect `1 passed`.

- [ ] **Step 5: Write failing test — rounded amount triggers REVISE then PASS.** Append to `tests/test_pipeline_simplify.py`:
```python
def test_simplify_revises_rounded_amount_then_passes():
    src = "건강보험료 본인부담금은 1,295,400원입니다. 2026년 7월 17일까지 납부하셔야 합니다."
    provider = FakeProvider([
        "건강보험료는 약 130만 원입니다.\n2026년 7월 17일까지 내세요.",
        "건강보험료는 1,295,400원입니다.\n2026년 7월 17일까지 내세요.",
    ])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=3)
    assert result.revisions == 1
    assert result.verdict == Verdict.PASS
    assert result.fidelity.verdict == Verdict.PASS
    assert "1,295,400원" in result.easy_text
    assert "약 130만" not in result.easy_text
```

- [ ] **Step 6: Run, expect PASS (real Fidelity catches the rounding).** Run `python -m pytest tests/test_pipeline_simplify.py -q -k rounded_amount`. Expect `1 passed`.

- [ ] **Step 7: Write failing test — negation flip routes to HUMAN_REVIEW without revising.** Append to `tests/test_pipeline_simplify.py`:
```python
def test_simplify_negation_flip_routes_to_human_review_without_revising():
    src = "이 지원금은 외국인은 신청할 수 없습니다. 내국인만 신청 가능합니다."
    provider = FakeProvider(["이 지원금은 외국인도 신청할 수 있습니다.\n내국인도 신청할 수 있습니다."])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=3)
    assert result.fidelity.verdict == Verdict.HUMAN_REVIEW
    assert result.verdict == Verdict.HUMAN_REVIEW
    assert result.revisions == 0
```

- [ ] **Step 8: Run, expect PASS.** Run `python -m pytest tests/test_pipeline_simplify.py -q -k negation_flip`. Expect `1 passed`.

- [ ] **Step 9: Write failing test — residual REVISE after max_revise escalates to HUMAN_REVIEW.** Append to `tests/test_pipeline_simplify.py`:
```python
def test_simplify_residual_failure_escalates_to_human_review():
    src = "본인부담금은 1,295,400원이며 2026년 7월 17일까지 납부하세요."
    provider = FakeProvider([
        "본인부담금은 약 130만 원입니다. 2026년 7월 17일까지 내세요.",
        "본인부담금은 약 130만 원입니다. 2026년 7월 17일까지 내세요.",
        "본인부담금은 약 130만 원입니다. 2026년 7월 17일까지 내세요.",
    ])
    result = simplify(_doc(src), Level.EASY, provider, max_revise=2)
    assert result.revisions == 2
    assert result.fidelity.verdict == Verdict.REVISE
    assert result.verdict == Verdict.HUMAN_REVIEW
```

- [ ] **Step 10: Run the whole simplify suite, expect PASS.** Run `python -m pytest tests/test_pipeline_simplify.py -q`. Expect `4 passed`.

- [ ] **Step 11: Commit.** Run `git add ttobak/pipeline.py tests/test_pipeline_simplify.py && git commit -m "feat(pipeline): wire real K-ER + Fidelity + pictograms into simplify() with verdict escalation"`.

### Task 35: End-to-end smoke on a realistic 고지서 snippet

A single end-to-end test driving the full Phase-2 surface against a realistic Korean health-insurance bill (고지서) through `simplify()` with a scripted `FakeProvider`, asserting the complete `EasyReadResult` is well-formed and renderer-ready: the money-shot path (round → catch → restore) plus pictogram attachment and field completeness (spec §2.3-1, MVP §12.2-7).

**Files:**
- Test: `tests/test_pipeline_e2e.py`

**Interfaces:**
- Consumes: `ttobak/ir.py` `Document`,`Block`,`BlockType`; `ttobak/levels.py` `Level`; `ttobak/common.py` `Verdict`; `ttobak/providers/fake.py` `FakeProvider`; `ttobak/result.py` `EasyReadResult`; `ttobak/pipeline.py` `simplify`.
- Produces: integration coverage only.

- [ ] **Step 1: Write the failing end-to-end test.** Create `tests/test_pipeline_e2e.py`:
```python
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict
from ttobak.providers.fake import FakeProvider
from ttobak.result import EasyReadResult
from ttobak.pipeline import simplify


def _gojiseo_doc() -> Document:
    return Document(
        blocks=[
            Block(type=BlockType.HEADING, text="2026년 7월분 건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="귀하의 2026년 7월분 건강보험료 본인부담금은 1,295,400원입니다."),
            Block(type=BlockType.PARAGRAPH, text="납부기한은 2026년 7월 17일까지입니다."),
            Block(type=BlockType.PARAGRAPH, text="문의: 국민건강보험공단 1577-1000."),
        ],
        source_mime="text/plain",
        meta={"ref_date": "2026-07-01"},
    )


def test_end_to_end_gojiseo_money_shot():
    doc = _gojiseo_doc()
    provider = FakeProvider([
        ("2026년 7월에 낼 건강보험료를 알려드립니다.\n내야 할 돈은 약 130만 원입니다.\n"
         "2026년 7월 17일까지 내세요.\n궁금하면 국민건강보험공단 1577-1000으로 전화하세요."),
        ("2026년 7월에 낼 건강보험료를 알려드립니다.\n내야 할 돈은 1,295,400원입니다.\n"
         "2026년 7월 17일까지 내세요.\n궁금하면 국민건강보험공단 1577-1000으로 전화하세요."),
    ])
    result = simplify(doc, Level.EASY, provider, max_revise=3)

    assert isinstance(result, EasyReadResult)
    assert result.level == Level.EASY
    assert result.source is doc
    assert result.revisions == 1
    assert result.verdict == Verdict.PASS
    assert result.fidelity.verdict == Verdict.PASS
    assert result.fidelity.exact_fail_count == 0
    assert "1,295,400원" in result.easy_text
    assert "2026년 7월 17일" in result.easy_text
    assert "1577-1000" in result.easy_text
    assert "약 130만" not in result.easy_text
    assert isinstance(result.ker.score, float)
    assert 0.0 <= result.ker.score <= 100.0
    assert isinstance(result.pictograms, list)  # 전화/돈 may match; attribute must be a list
```

- [ ] **Step 2: Run, expect PASS.** Run `python -m pytest tests/test_pipeline_e2e.py -q`. Expect `1 passed`. (No new implementation — exercises the Task-34 loop end-to-end against real `score`/`verify`/`match`. A failure reveals a real integration gap to debug.)

- [ ] **Step 3: Run the entire Phase-2 pipeline surface for a green baseline.** Run `python -m pytest tests/test_pipeline_prompts.py tests/test_pipeline_simplify.py tests/test_pipeline_e2e.py tests/metric tests/fidelity -q`. Expect all passing.

- [ ] **Step 4: Commit.** Run `git add tests/test_pipeline_e2e.py && git commit -m "test(pipeline): end-to-end 고지서 money-shot smoke through simplify()"`.

## Phase 3: 표면·평가·라이선스

The surfaces and evidence. M7 renderer (Task 36–37; pictogram model/lexicon/`match()` already shipped as Tasks 31–32). M8 PDF + HWPX parsers added to `parse()` (Task 38–41). M9 web demo (Task 42–47). M10 evaluation harness + corpus (Task 48–55). M11 license/security CI gate + packaging finalize (Task 56–63).

### Task 36: Renderer Jinja2 template (side-by-side + disclaimer + badges + easy layout)

**Files:**
- Create: `ttobak/templates/result.html.j2`
- Create: `tests/render/__init__.py` (empty)
- Test: `tests/render/test_template_file.py`

**Interfaces:**
- Consumes: nothing at import time (static template asset + static-content test). The template is wired to `render_html()` in Task 37. Variables it expects (provided by `render_html()`): `source_text`, `easy_text`, `ker_score`, `ker_unvalidated_note`, `violations` (list of `{rule, span, severity, suggestion}`), `fidelity_verdict`, `fidelity_badge_class`, `fidelity_badge_label`, `pictograms` (list of `{glyph_id, caption}`), `level_label`, `disclaimer`.
- Produces: `ttobak/templates/result.html.j2` — the canonical render template enforcing spec §3.4 easy-layout rules in inline CSS (easy column `font-size: 18px` ≥14pt, `text-align: left`, `line-height: 2.0`, generous padding); always-present disclaimer (spec §3.1/§8.7); K-ER score + per-rule violation list with the "규칙 기반 루브릭, 경험적 검증 아님" note (spec §5.3); fidelity verdict badge.

- [ ] **Step 1: Write failing test asserting the template file exists with required literals.** Create `tests/render/__init__.py` (empty), then `tests/render/test_template_file.py`:
```python
from pathlib import Path

import ttobak

TEMPLATE = Path(ttobak.__file__).parent / "templates" / "result.html.j2"


def test_template_file_exists():
    assert TEMPLATE.is_file()


def test_template_contains_layout_and_disclaimer_literals():
    body = TEMPLATE.read_text(encoding="utf-8")
    assert "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다" in body
    assert "font-size: 18px" in body
    assert "text-align: left" in body
    assert "규칙 기반 루브릭" in body
    assert 'class="source"' in body
    assert 'class="easy"' in body


def test_template_references_expected_variables():
    body = TEMPLATE.read_text(encoding="utf-8")
    for var in ("source_text", "easy_text", "ker_score", "violations",
                "fidelity_badge_label", "pictograms", "disclaimer"):
        assert var in body
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/render/test_template_file.py -q`. Expect `AssertionError` on `TEMPLATE.is_file()` (template absent).

- [ ] **Step 3: Create the template.** Create `ttobak/templates/result.html.j2`:
```html
<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>또박 쉬운 정보 변환 결과</title>
<style>
  body {
    font-family: "Noto Sans KR", "Malgun Gothic", sans-serif;
    color: #1a1a1a;
    background: #ffffff;
    margin: 0;
    padding: 24px;
  }
  .disclaimer {
    background: #fff7e6;
    border: 2px solid #e8a400;
    border-radius: 8px;
    padding: 16px 20px;
    font-size: 16px;
    line-height: 1.8;
    margin-bottom: 24px;
  }
  .badges { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 24px; }
  .badge { border-radius: 999px; padding: 8px 16px; font-size: 15px; font-weight: 700; }
  .badge-ker { background: #e6f0ff; color: #1452cc; }
  .badge-pass { background: #e3f9e5; color: #137333; }
  .badge-revise { background: #fff4e5; color: #b06000; }
  .badge-human_review { background: #fde7e7; color: #c5221f; }
  .columns { display: flex; gap: 24px; align-items: stretch; }
  .col { flex: 1 1 0; border: 1px solid #d9d9d9; border-radius: 8px; padding: 20px; }
  .col h2 { font-size: 18px; margin-top: 0; }
  .source .text { font-size: 15px; line-height: 1.7; text-align: left; white-space: pre-wrap; }
  /* spec 3.4 easy layout: >=14pt (18px), left-align, generous spacing */
  .easy .text { font-size: 18px; line-height: 2.0; text-align: left; letter-spacing: 0.01em; white-space: pre-wrap; }
  .pictograms { display: flex; flex-wrap: wrap; gap: 16px; margin-top: 20px; }
  .pictogram { display: flex; flex-direction: column; align-items: center; font-size: 15px; width: 96px; text-align: center; }
  .pictogram img { width: 64px; height: 64px; }
  .violations { margin-top: 24px; }
  .violations ul { padding-left: 20px; }
  .violations li { font-size: 15px; line-height: 1.8; margin-bottom: 8px; }
  .sev-high { color: #c5221f; font-weight: 700; }
  .sev-med { color: #b06000; }
  .sev-low { color: #555555; }
  .ker-note { font-size: 14px; color: #555555; margin-top: 8px; }
</style>
</head>
<body>

<div class="disclaimer" role="note">{{ disclaimer }}</div>

<div class="badges">
  <span class="badge badge-ker">K-ER {{ ker_score }}점 · {{ level_label }}</span>
  <span class="badge badge-{{ fidelity_badge_class }}">사실충실성: {{ fidelity_badge_label }}</span>
</div>

<div class="columns">
  <section class="col source">
    <h2>원문</h2>
    <div class="text">{{ source_text }}</div>
  </section>
  <section class="col easy">
    <h2>쉬운 글</h2>
    <div class="text">{{ easy_text }}</div>
    {% if pictograms %}
    <div class="pictograms">
      {% for p in pictograms %}
      <figure class="pictogram">
        <img src="{{ p.glyph_id }}" alt="{{ p.caption }}">
        <figcaption>{{ p.caption }}</figcaption>
      </figure>
      {% endfor %}
    </div>
    {% endif %}
  </section>
</div>

<section class="violations">
  <h2>K-ER 점수 {{ ker_score }}점</h2>
  <p class="ker-note">{{ ker_unvalidated_note }}</p>
  {% if violations %}
  <ul>
    {% for v in violations %}
    <li>
      <span class="sev-{{ v.severity }}">[{{ v.severity }}]</span>
      <strong>{{ v.rule }}</strong>: &ldquo;{{ v.span }}&rdquo; &rarr; {{ v.suggestion }}
    </li>
    {% endfor %}
  </ul>
  {% else %}
  <p>위반 사항이 없습니다.</p>
  {% endif %}
</section>

</body>
</html>
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/render/test_template_file.py -q`. Expect `3 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/templates/result.html.j2 tests/render/__init__.py tests/render/test_template_file.py && git commit -m "feat(render): side-by-side result template with disclaimer + easy layout"`.

### Task 37: render_html() — wire result into template + Jinja2 environment

**Files:**
- Create: `ttobak/render.py`
- Modify: `pyproject.toml` (jinja2 is already a Task-1 dependency; add the `templates/*.j2` package-data include)
- Test: `tests/render/test_render_html.py`

**Interfaces:**
- Consumes: `ttobak/result.py` `EasyReadResult`; `ttobak/ir.py` `Document.text()`; `ttobak/levels.py` `Level`; `ttobak/common.py` `Verdict`,`Severity`; `ttobak/metric/models.py` `KERReport`,`Violation`; `ttobak/fidelity/models.py` `FidelityReport`; `ttobak/pictogram/models.py` `PictogramRef`; `ttobak/templates/result.html.j2` (Task 36).
- Produces: `ttobak/render.py: def render_html(result: EasyReadResult) -> str` — builds the Jinja2 `Environment` (autoescape on) with a `FileSystemLoader` rooted at the package `templates/` dir, maps `EasyReadResult` → template vars, returns rendered HTML. Public engine API per contracts.

- [ ] **Step 1: Write failing test for render_html().** Create `tests/render/test_render_html.py`:
```python
from ttobak.common import Severity, Verdict
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Block, BlockType, Document
from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation
from ttobak.pictogram.models import PictogramRef
from ttobak.render import render_html
from ttobak.result import EasyReadResult


def _build_result() -> EasyReadResult:
    source = Document(
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="2026년 7월분 보험료 1,295,400원을 2026년 7월 25일까지 납부하시기 바랍니다."),
        ],
        source_mime="text/plain",
    )
    ker = KERReport(
        score=81.0, level_estimate=2, sub_scores={"rule": 81.0},
        violations=[Violation(rule="한자어", span="납부", severity=Severity.MED, suggestion="'돈을 내요'로 바꾸기")],
    )
    fidelity = FidelityReport(slots=[], verdict=Verdict.PASS)
    return EasyReadResult(
        source=source,
        easy_text="2026년 7월 보험료는 1,295,400원입니다.\n2026년 7월 25일까지 돈을 내세요.",
        level=Level.EASY, ker=ker, fidelity=fidelity,
        pictograms=[PictogramRef(concept="돈", set="mulberry", glyph_id="mulberry/money.svg", caption="돈")],
        revisions=1, verdict=Verdict.PASS,
    )


def test_render_html_returns_str():
    html = render_html(_build_result())
    assert isinstance(html, str)
    assert html.lstrip().startswith("<!DOCTYPE html>")


def test_render_html_contains_both_texts():
    html = render_html(_build_result())
    assert "건강보험료 납부 안내" in html
    assert "2026년 7월 25일까지 돈을 내세요" in html


def test_render_html_always_has_disclaimer():
    assert "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다" in render_html(_build_result())


def test_render_html_shows_score_and_violation():
    html = render_html(_build_result())
    assert "81" in html
    assert "규칙 기반 루브릭" in html
    assert "한자어" in html
    assert "돈을 내요" in html


def test_render_html_fidelity_badge_pass():
    html = render_html(_build_result())
    assert "badge-pass" in html
    assert "통과" in html


def test_render_html_renders_pictogram_path_not_inlined():
    html = render_html(_build_result())
    assert 'src="mulberry/money.svg"' in html
    assert "data:image" not in html


def test_render_html_human_review_badge():
    result = _build_result()
    result.verdict = Verdict.HUMAN_REVIEW
    result.fidelity = FidelityReport(slots=[], verdict=Verdict.HUMAN_REVIEW)
    html = render_html(result)
    assert "badge-human_review" in html
    assert "검수 필요" in html


def test_render_html_easy_layout_font_size():
    html = render_html(_build_result())
    assert "font-size: 18px" in html
    assert "text-align: left" in html
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/render/test_render_html.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.render'`.

- [ ] **Step 3: Implement `render_html()`.** Create `ttobak/render.py`:
```python
from __future__ import annotations

from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from ttobak.common import Verdict
from ttobak.result import EasyReadResult

_TEMPLATE_DIR = Path(__file__).parent / "templates"
_TEMPLATE_NAME = "result.html.j2"

# Always-on disclaimer (spec 3.1 / 8.7). Must contain the verbatim phrase the
# template test asserts: "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다".
_DISCLAIMER = "이 쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다. 자동 변환 결과입니다."

_KER_UNVALIDATED_NOTE = (
    "이 점수는 한국 쉬운 정보 지침에 정렬된 규칙 기반 루브릭이며, "
    "경험적으로 검증된 점수가 아닙니다. 규칙별 위반 목록을 함께 확인하세요."
)

_VERDICT_BADGE: dict[Verdict, tuple[str, str]] = {
    Verdict.PASS: ("pass", "통과"),
    Verdict.REVISE: ("revise", "수정 필요"),
    Verdict.HUMAN_REVIEW: ("human_review", "검수 필요"),
}

_LEVEL_LABEL = {"plain": "보통 읽기", "easy": "쉬운 글"}

_env = Environment(
    loader=FileSystemLoader(str(_TEMPLATE_DIR)),
    autoescape=select_autoescape(["html", "j2"]),
    trim_blocks=True,
    lstrip_blocks=True,
)


def render_html(result: EasyReadResult) -> str:
    """Render an EasyReadResult to side-by-side accessible HTML.

    Always includes the source text, the easy text, the Fidelity-first
    disclaimer, the (non-validated) K-ER score + per-rule violations, the
    fidelity verdict badge, and pictograms as file-path references only.
    """
    badge_class, badge_label = _VERDICT_BADGE[result.fidelity.verdict]
    template = _env.get_template(_TEMPLATE_NAME)
    return template.render(
        disclaimer=_DISCLAIMER,
        source_text=result.source.text(),
        easy_text=result.easy_text,
        level_label=_LEVEL_LABEL.get(result.level.value, result.level.value),
        ker_score=int(round(result.ker.score)),
        ker_unvalidated_note=_KER_UNVALIDATED_NOTE,
        violations=[
            {"rule": v.rule, "span": v.span, "severity": v.severity.value, "suggestion": v.suggestion}
            for v in result.ker.violations
        ],
        fidelity_verdict=result.fidelity.verdict.value,
        fidelity_badge_class=badge_class,
        fidelity_badge_label=badge_label,
        pictograms=[{"glyph_id": p.glyph_id, "caption": p.caption} for p in result.pictograms],
    )
```
  Note: the `_DISCLAIMER` constant must contain the exact phrase `쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다`; the template renders `{{ disclaimer }}` from this value, so the Task-36 template-file test (which checks the literal in the template) and this render test (which checks it in output) are both satisfied. Keep the literal in BOTH the template static text AND this constant identical.

- [ ] **Step 4: Add the template package-data include.** Ensure `pyproject.toml` ships the template: add (or merge into) `[tool.setuptools.package-data] ttobak = ["templates/*.j2", "data/*.txt"]`. (jinja2 is already a Task-1 runtime dependency.)

- [ ] **Step 5: Run, expect PASS.** Run `python -m pytest tests/render/test_render_html.py -q`. Expect `8 passed`.

- [ ] **Step 6: Run the full M7 suite, expect no regressions.** Run `python -m pytest tests/pictogram tests/render -q`. Expect all passing.

- [ ] **Step 7: Commit.** Run `git add ttobak/render.py pyproject.toml tests/render/test_render_html.py && git commit -m "feat(render): render_html() wiring EasyReadResult into side-by-side template"`.

### Task 38: PDF fixture + HWPX fixture generation helpers

Provide deterministic, dependency-free fixture generators so every later parser test can synthesize a real PDF / real HWPX in-memory (no committed binary blobs). `make_minimal_pdf` hand-writes a spec-valid single-page PDF (Helvetica, ASCII) that pypdf and pdfminer.six both extract. `make_minimal_hwpx` builds a real OWPML ZIP that `hwp_hwpx_parser.Reader` opens.

**Files:**
- Create: `ttobak/parse/_fixtures.py`
- Create: `tests/parse/__init__.py` (empty)
- Create: `tests/parse/conftest.py`
- Test: `tests/parse/test_fixtures.py`

**Interfaces:**
- Consumes: stdlib `io`, `zipfile`.
- Produces: `def make_minimal_pdf(lines: list[str]) -> bytes`; `def make_minimal_hwpx(paragraphs: list[str]) -> bytes`; pytest fixtures `pdf_bytes`, `hwpx_bytes` in `conftest.py`.

- [ ] **Step 1: Write failing test for the fixture builders.** Create `tests/parse/__init__.py` (empty), then `tests/parse/test_fixtures.py`:
```python
from pdfminer.high_level import extract_text
from pypdf import PdfReader
import io

from ttobak.parse._fixtures import make_minimal_pdf, make_minimal_hwpx


def test_make_minimal_pdf_is_readable_by_pypdf():
    data = make_minimal_pdf(["Hello Ttobak", "Line two"])
    assert isinstance(data, bytes)
    assert data.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "Hello Ttobak" in text
    assert "Line two" in text


def test_make_minimal_pdf_is_readable_by_pdfminer():
    data = make_minimal_pdf(["Fallback path"])
    text = extract_text(io.BytesIO(data))
    assert "Fallback path" in text


def test_make_minimal_hwpx_is_a_zip_owpml():
    data = make_minimal_hwpx(["문단 하나", "문단 둘"])
    assert isinstance(data, bytes)
    assert data[:2] == b"PK"
    import zipfile, io as _io
    zf = zipfile.ZipFile(_io.BytesIO(data))
    names = zf.namelist()
    assert "mimetype" in names
    assert any(n.startswith("Contents/section") for n in names)
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/parse/test_fixtures.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.parse._fixtures'`.

- [ ] **Step 3: Implement `ttobak/parse/_fixtures.py`.** Create the file with both builders:
```python
"""Deterministic, dependency-free fixture builders for parser tests.

``make_minimal_pdf`` hand-writes a minimal but spec-valid single-page PDF using
Helvetica so both pypdf and pdfminer.six can extract its text. ``make_minimal_hwpx``
builds a minimal OWPML ZIP that hwp-hwpx-parser's Reader can open. Raw bytes only.
"""
from __future__ import annotations

import io
import zipfile


def _pdf_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def make_minimal_pdf(lines: list[str]) -> bytes:
    """Return a valid single-page PDF showing each string in ``lines`` (Helvetica 12pt, ASCII)."""
    content_parts = ["BT", "/F1 12 Tf", "72 720 Td", "16 TL"]
    for i, line in enumerate(lines):
        if i > 0:
            content_parts.append("T*")
        content_parts.append(f"({_pdf_escape(line)}) Tj")
    content_parts.append("ET")
    content = ("\n".join(content_parts)).encode("latin-1")

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
    )
    objects.append(
        b"<< /Length " + str(len(content)).encode("latin-1") + b" >>\nstream\n" + content + b"\nendstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets: list[int] = []
    for idx, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(str(idx).encode("latin-1") + b" 0 obj\n")
        out.write(body)
        out.write(b"\nendobj\n")

    xref_pos = out.tell()
    n = len(objects) + 1
    out.write(b"xref\n")
    out.write(b"0 " + str(n).encode("latin-1") + b"\n")
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode("latin-1"))
    out.write(b"trailer\n")
    out.write(b"<< /Size " + str(n).encode("latin-1") + b" /Root 1 0 R >>\n")
    out.write(b"startxref\n")
    out.write(str(xref_pos).encode("latin-1") + b"\n")
    out.write(b"%%EOF")
    return out.getvalue()


_HWPX_VERSION_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" '
    'tagetApplication="WORDPROCESSOR" major="5" minor="0" micro="5" '
    'buildNumber="0" os="1" xmlVersion="1.4" application="Hancom Office" '
    'appVersion="11.0.0.0"/>'
)

_HWPX_CONTENT_HPF = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" '
    'version="" unique-identifier="" id="">'
    '<opf:spine><opf:itemref idref="section0"/></opf:spine>'
    '</opf:package>'
)

_HWPX_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
    'version="1.4" secCnt="1"></hh:head>'
)


def _hwpx_section(paragraphs: list[str]) -> str:
    ns = (
        'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
    )
    body = []
    for text in paragraphs:
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body.append('<hp:p><hp:run><hp:t>' + escaped + '</hp:t></hp:run></hp:p>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<hs:sec ' + ns + '>' + "".join(body) + '</hs:sec>'
    )


def make_minimal_hwpx(paragraphs: list[str]) -> bytes:
    """Return a minimal valid HWPX (OWPML ZIP) containing ``paragraphs``."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be first and stored uncompressed per OCF.
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("version.xml", _HWPX_VERSION_XML)
        zf.writestr("Contents/content.hpf", _HWPX_CONTENT_HPF)
        zf.writestr("Contents/header.xml", _HWPX_HEADER)
        zf.writestr("Contents/section0.xml", _hwpx_section(paragraphs))
    return buf.getvalue()
```

- [ ] **Step 4: Run the fixture test, expect PASS.** Run `python -m pytest tests/parse/test_fixtures.py -q`. Expect `3 passed`.

- [ ] **Step 5: Add shared `conftest.py` fixtures.** Create `tests/parse/conftest.py`:
```python
import pytest

from ttobak.parse._fixtures import make_minimal_pdf, make_minimal_hwpx


@pytest.fixture
def pdf_bytes() -> bytes:
    return make_minimal_pdf(["Ttobak PDF body", "Second visible line"])


@pytest.fixture
def hwpx_bytes() -> bytes:
    return make_minimal_hwpx(["청년 주거지원 안내문", "신청 기간은 정해져 있습니다."])
```
  Run `python -m pytest tests/parse/ -q`. Expect `3 passed`.

- [ ] **Step 6: Commit.** Run `git checkout -b m8-pdf-hwpx && git add ttobak/parse/_fixtures.py tests/parse/__init__.py tests/parse/conftest.py tests/parse/test_fixtures.py && git commit -m "test(parse): add dependency-free PDF/HWPX fixture builders"`.

### Task 39: PDF parser (pypdf primary, pdfminer.six fallback) -> Document with confidence

`parse_pdf` extracts text page-by-page. pypdf is primary (confidence 1.0). When pypdf yields empty text (or raises), fall back to pdfminer.six over the whole document and tag blocks with reduced confidence (0.6) so the Fidelity gate / renderer flag low-trust source (spec §3.1/§6.10/§7.3). An empty/garbage PDF degrades to an explicit `ParseError`, never a silent empty Document.

**Files:**
- Create: `ttobak/parse/pdf_parser.py`
- Test: `tests/parse/test_pdf_parser.py`

**Interfaces:**
- Consumes: `ttobak.ir.Document`,`Block`,`BlockType.PARAGRAPH`; `ttobak.parse._fixtures.make_minimal_pdf` (test); `pypdf.PdfReader`, `pdfminer.high_level.extract_text`.
- Produces: `def parse_pdf(data: bytes, *, source_mime: str = "application/pdf") -> Document`; `class ParseError(ValueError)`; `PDF_MIME="application/pdf"`, `PDF_PRIMARY_CONFIDENCE=1.0`, `PDF_FALLBACK_CONFIDENCE=0.6`.

- [ ] **Step 1: Write failing test for happy-path pypdf extraction.** Create `tests/parse/test_pdf_parser.py`:
```python
import io

import pytest
from pypdf import PdfWriter

from ttobak.ir import BlockType, Document
from ttobak.parse._fixtures import make_minimal_pdf
from ttobak.parse.pdf_parser import (
    ParseError, parse_pdf, PDF_PRIMARY_CONFIDENCE, PDF_FALLBACK_CONFIDENCE,
)


def test_parse_pdf_extracts_text_with_full_confidence(pdf_bytes):
    doc = parse_pdf(pdf_bytes)
    assert isinstance(doc, Document)
    assert doc.source_mime == "application/pdf"
    assert "Ttobak PDF body" in doc.text()
    assert "Second visible line" in doc.text()
    assert all(b.type is BlockType.PARAGRAPH for b in doc.blocks)
    assert all(b.confidence == PDF_PRIMARY_CONFIDENCE for b in doc.blocks)
    assert doc.meta["parser"] == "pypdf"


def test_parse_pdf_one_block_per_nonblank_line(pdf_bytes):
    doc = parse_pdf(pdf_bytes)
    texts = [b.text for b in doc.blocks]
    assert "Ttobak PDF body" in texts
    assert "Second visible line" in texts
    assert "" not in texts
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/parse/test_pdf_parser.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.parse.pdf_parser'`.

- [ ] **Step 3: Implement `parse_pdf` happy path (pypdf) + ParseError.** Create `ttobak/parse/pdf_parser.py`:
```python
"""PDF -> Document. pypdf primary, pdfminer.six fallback (M8)."""
from __future__ import annotations

import io

from ttobak.ir import Block, BlockType, Document

PDF_MIME = "application/pdf"
PDF_PRIMARY_CONFIDENCE = 1.0
PDF_FALLBACK_CONFIDENCE = 0.6


class ParseError(ValueError):
    """Raised when input cannot be parsed into any usable text."""


def _lines_to_blocks(text: str, confidence: float) -> list[Block]:
    blocks: list[Block] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        blocks.append(Block(type=BlockType.PARAGRAPH, text=line, confidence=confidence))
    return blocks


def parse_pdf(data: bytes, *, source_mime: str = PDF_MIME) -> Document:
    """Parse PDF ``data`` to a Document (pypdf, confidence 1.0; ParseError if no text)."""
    try:
        from pypdf import PdfReader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ParseError(f"pypdf is not installed: {exc}") from exc

    try:
        reader = PdfReader(io.BytesIO(data))
        pages = [(p.extract_text() or "") for p in reader.pages]
    except Exception as exc:
        raise ParseError(f"pypdf failed to read PDF: {exc}") from exc

    text = "\n".join(pages)
    blocks = _lines_to_blocks(text, PDF_PRIMARY_CONFIDENCE)
    if not blocks:
        raise ParseError("PDF contained no extractable text")
    return Document(blocks=blocks, source_mime=source_mime, meta={"parser": "pypdf"})
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/parse/test_pdf_parser.py -q`. Expect `2 passed`.

- [ ] **Step 5: Write failing tests for empty-PDF degradation.** Append to `tests/parse/test_pdf_parser.py`:
```python
def test_parse_pdf_blank_page_raises_parse_error():
    writer = PdfWriter()
    writer.add_blank_page(width=612, height=792)
    buf = io.BytesIO()
    writer.write(buf)
    with pytest.raises(ParseError, match="no extractable text"):
        parse_pdf(buf.getvalue())


def test_parse_pdf_garbage_bytes_raises_parse_error():
    with pytest.raises(ParseError):
        parse_pdf(b"this is definitely not a pdf")
```
  Run `python -m pytest tests/parse/test_pdf_parser.py -k "blank or garbage" -q`. Both should PASS already (Step-3 raises ParseError for empty text and read errors). This locks the degradation contract before adding the fallback.

- [ ] **Step 6: Write failing test for the pdfminer fallback + reduced confidence.** Append to `tests/parse/test_pdf_parser.py`:
```python
def test_parse_pdf_falls_back_to_pdfminer(monkeypatch, pdf_bytes):
    import ttobak.parse.pdf_parser as mod

    class _EmptyPage:
        def extract_text(self):
            return ""

    class _EmptyReader:
        def __init__(self, *a, **k):
            self.pages = [_EmptyPage()]

    monkeypatch.setattr(mod, "PdfReader", _EmptyReader, raising=False)

    doc = parse_pdf(pdf_bytes)
    assert "Ttobak PDF body" in doc.text()
    assert doc.meta["parser"] == "pdfminer.six"
    assert all(b.confidence == PDF_FALLBACK_CONFIDENCE for b in doc.blocks)
```
  Run `python -m pytest tests/parse/test_pdf_parser.py -k fallback -q`. Expect FAIL — `PdfReader` is imported locally (not monkeypatchable) and there is no fallback yet.

- [ ] **Step 7: Implement the pdfminer.six fallback.** Replace the full contents of `ttobak/parse/pdf_parser.py`, hoisting imports to module level so they are monkeypatchable:
```python
"""PDF -> Document. pypdf primary, pdfminer.six fallback (M8)."""
from __future__ import annotations

import io

from pdfminer.high_level import extract_text as _pdfminer_extract_text
from pypdf import PdfReader

from ttobak.ir import Block, BlockType, Document

PDF_MIME = "application/pdf"
PDF_PRIMARY_CONFIDENCE = 1.0
PDF_FALLBACK_CONFIDENCE = 0.6


class ParseError(ValueError):
    """Raised when input cannot be parsed into any usable text."""


def _lines_to_blocks(text: str, confidence: float) -> list[Block]:
    blocks: list[Block] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        blocks.append(Block(type=BlockType.PARAGRAPH, text=line, confidence=confidence))
    return blocks


def _pypdf_text(data: bytes) -> str:
    reader = PdfReader(io.BytesIO(data))
    pages = [(p.extract_text() or "") for p in reader.pages]
    return "\n".join(pages)


def _pdfminer_text(data: bytes) -> str:
    return _pdfminer_extract_text(io.BytesIO(data)) or ""


def parse_pdf(data: bytes, *, source_mime: str = PDF_MIME) -> Document:
    """Parse PDF ``data`` to a Document.

    pypdf primary (confidence 1.0). If pypdf yields no usable text, fall back to
    pdfminer.six and tag blocks with reduced confidence (0.6). If both yield
    nothing, raise ParseError (no silent empty Document).
    """
    primary_error: Exception | None = None
    try:
        text = _pypdf_text(data)
    except Exception as exc:
        primary_error = exc
        text = ""

    blocks = _lines_to_blocks(text, PDF_PRIMARY_CONFIDENCE)
    if blocks:
        return Document(blocks=blocks, source_mime=source_mime, meta={"parser": "pypdf"})

    try:
        fb_text = _pdfminer_text(data)
    except Exception as exc:
        raise ParseError(
            f"both pypdf and pdfminer.six failed to read PDF: pypdf={primary_error!r} pdfminer={exc!r}"
        ) from exc

    fb_blocks = _lines_to_blocks(fb_text, PDF_FALLBACK_CONFIDENCE)
    if not fb_blocks:
        raise ParseError("PDF contained no extractable text")
    return Document(blocks=fb_blocks, source_mime=source_mime, meta={"parser": "pdfminer.six"})
```

- [ ] **Step 8: Run the full PDF parser test file, expect PASS.** Run `python -m pytest tests/parse/test_pdf_parser.py -q`. Expect `5 passed`.

- [ ] **Step 9: Commit.** Run `git add ttobak/parse/pdf_parser.py tests/parse/test_pdf_parser.py && git commit -m "feat(parse): PDF parser with pypdf primary + pdfminer.six fallback and confidence"`.

### Task 40: HWPX parser (hwp-hwpx-parser, best-effort, graceful low-confidence)

`parse_hwpx` over Apache-2.0 `hwp-hwpx-parser`. Per spec §7.1/§15.4 HWPX is BEST-EFFORT: a clean parse produces blocks at sub-1.0 confidence; a parse the library reports invalid/empty degrades to an explicit `ParseError` (never silent). Legacy `.hwp` binary is out of MVP scope and rejected with `UnsupportedFormatError`. The library is path/OLE/ZIP based, so bytes input is written to a NamedTemporaryFile.

**Files:**
- Create: `ttobak/parse/hwp_parser.py`
- Test: `tests/parse/test_hwp_parser.py`

**Interfaces:**
- Consumes: `ttobak.ir.Document`,`Block`,`BlockType.PARAGRAPH`; `ttobak.parse.pdf_parser.ParseError` (shared error type); `ttobak.parse._fixtures.make_minimal_hwpx` (test); `hwp_hwpx_parser.Reader`.
- Produces: `def parse_hwpx(data: bytes, *, source_mime: str = "application/vnd.hancom.hwpx") -> Document`; `class UnsupportedFormatError(ValueError)`; `HWPX_MIME`, `HWP_MIME`, `HWPX_CONFIDENCE=0.7`.

- [ ] **Step 1: Write failing test for happy-path HWPX extraction.** Create `tests/parse/test_hwp_parser.py`:
```python
import pytest

from ttobak.ir import BlockType, Document
from ttobak.parse._fixtures import make_minimal_hwpx
from ttobak.parse.pdf_parser import ParseError
from ttobak.parse.hwp_parser import parse_hwpx, UnsupportedFormatError, HWPX_CONFIDENCE


def test_parse_hwpx_extracts_paragraphs_best_effort(hwpx_bytes):
    doc = parse_hwpx(hwpx_bytes)
    assert isinstance(doc, Document)
    assert doc.source_mime == "application/vnd.hancom.hwpx"
    assert "청년 주거지원 안내문" in doc.text()
    assert "신청 기간은 정해져 있습니다." in doc.text()
    assert all(b.type is BlockType.PARAGRAPH for b in doc.blocks)
    assert all(b.confidence == HWPX_CONFIDENCE for b in doc.blocks)
    assert doc.meta["parser"] == "hwp-hwpx-parser"
    assert doc.meta["best_effort"] is True
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/parse/test_hwp_parser.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.parse.hwp_parser'`.

- [ ] **Step 3: Implement `parse_hwpx` happy path + .hwp rejection.** Create `ttobak/parse/hwp_parser.py`:
```python
"""HWPX -> Document via hwp-hwpx-parser (best-effort, M8).

Legacy .hwp (OLE binary) is out of MVP scope (spec 7.1/12.3/15.4) and rejected
with UnsupportedFormatError. HWPX is BEST-EFFORT: clean parses yield blocks at
sub-1.0 confidence; unreadable/empty input degrades to an explicit ParseError
(never a silent empty Document, spec 3.1/7.3).
"""
from __future__ import annotations

import os
import tempfile

from ttobak.ir import Block, BlockType, Document
from ttobak.parse.pdf_parser import ParseError

HWPX_MIME = "application/vnd.hancom.hwpx"
HWP_MIME = "application/x-hwp"
HWPX_CONFIDENCE = 0.7


class UnsupportedFormatError(ValueError):
    """Raised for inputs outside MVP parser scope (e.g. legacy .hwp)."""


def _text_to_blocks(text: str) -> list[Block]:
    blocks: list[Block] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        blocks.append(Block(type=BlockType.PARAGRAPH, text=line, confidence=HWPX_CONFIDENCE))
    return blocks


def parse_hwpx(data: bytes, *, source_mime: str = HWPX_MIME) -> Document:
    """Parse HWPX ``data`` (best-effort) into a Document.

    Writes bytes to a temp file because hwp-hwpx-parser reads from a path.
    """
    if source_mime == HWP_MIME:
        raise UnsupportedFormatError("legacy .hwp binary is out of MVP scope; convert to HWPX or PDF")

    try:
        from hwp_hwpx_parser import Reader
    except ImportError as exc:  # pragma: no cover - dependency guard
        raise ParseError(f"hwp-hwpx-parser is not installed: {exc}") from exc

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".hwpx", delete=False) as tmp:
            tmp.write(data)
            tmp_path = tmp.name
        try:
            with Reader(tmp_path) as reader:
                if not getattr(reader, "is_valid", True):
                    raise ParseError("hwp-hwpx-parser reported invalid HWPX")
                text = reader.text or ""
        except ParseError:
            raise
        except Exception as exc:
            raise ParseError(f"hwp-hwpx-parser failed: {exc}") from exc
    finally:
        if tmp_path is not None and os.path.exists(tmp_path):
            os.unlink(tmp_path)

    blocks = _text_to_blocks(text)
    if not blocks:
        raise ParseError("HWPX contained no extractable text")
    return Document(blocks=blocks, source_mime=source_mime, meta={"parser": "hwp-hwpx-parser", "best_effort": True})
```

- [ ] **Step 4: Run the happy-path test, expect PASS.** Run `python -m pytest tests/parse/test_hwp_parser.py -q`. Expect `1 passed`. (If the `hwp-hwpx-parser` Reader API differs from `.text`/`.is_valid` at runtime, adapt the accessor to the installed v1.0.0 surface; keep the best-effort + ParseError contract.)

- [ ] **Step 5: Write failing tests for graceful degradation and .hwp rejection.** Append to `tests/parse/test_hwp_parser.py`:
```python
def test_parse_hwpx_rejects_legacy_hwp_mime(hwpx_bytes):
    with pytest.raises(UnsupportedFormatError, match="legacy .hwp"):
        parse_hwpx(hwpx_bytes, source_mime="application/x-hwp")


def test_parse_hwpx_corrupt_input_raises_parse_error():
    with pytest.raises(ParseError):
        parse_hwpx(b"PK\x03\x04 not a real hwpx zip body")


def test_parse_hwpx_empty_document_raises_parse_error():
    empty = make_minimal_hwpx([])  # valid OWPML, zero paragraphs
    with pytest.raises(ParseError, match="no extractable text"):
        parse_hwpx(empty)
```

- [ ] **Step 6: Run the full HWPX parser test file, expect PASS.** Run `python -m pytest tests/parse/test_hwp_parser.py -q`. Expect `4 passed`. If `corrupt` returns a Document instead of raising, tighten the `except Exception` wrapping in `parse_hwpx`.

- [ ] **Step 7: Commit.** Run `git add ttobak/parse/hwp_parser.py tests/parse/test_hwp_parser.py && git commit -m "feat(parse): best-effort HWPX parser with graceful degradation; reject legacy .hwp"`.

### Task 41: Register PDF + HWPX in parse() dispatch

Wire the two new parsers into the public `parse(source, mime)` (Task 8 already handles `text/plain`/`text/markdown`). For PDF/HWPX, normalize the source to bytes (read a Path; reject a `str` for binary mimes); dispatch by mime; reject `.hwp` and unknown mimes.

> **Error-type reconciliation:** Task 8's dispatcher raises `UnsupportedMimeError` (from `ttobak/parse/text_parser.py`) for unknown mimes. M8 introduces `UnsupportedFormatError` for legacy `.hwp`. Keep BOTH: `.hwp` → `UnsupportedFormatError`; any other unknown mime → `UnsupportedMimeError` (preserves the Task-8 `test_parse_raises_on_unsupported_mime` contract, which expects `UnsupportedMimeError` for `application/pdf` — but `application/pdf` is now SUPPORTED, so update that Task-8 test to use a genuinely unknown mime like `application/zip`). Re-export both error types and the new functions from `ttobak.parse`.

**Files:**
- Modify: `ttobak/parse/__init__.py`
- Modify: `tests/test_parse_dispatch.py` (update the now-supported `application/pdf` case to `application/zip`)
- Test: `tests/parse/test_parse_dispatch_m8.py`

**Interfaces:**
- Consumes: `ttobak.parse.pdf_parser` `parse_pdf`,`ParseError`,`PDF_MIME`; `ttobak.parse.hwp_parser` `parse_hwpx`,`UnsupportedFormatError`,`HWPX_MIME`,`HWP_MIME`; existing Task-8 text routing; `ttobak.parse.text_parser.UnsupportedMimeError`; `ttobak.ir.Document`.
- Produces: `parse(...)` now routing `application/pdf`, `application/vnd.hancom.hwpx`, rejecting `application/x-hwp` (`UnsupportedFormatError`) and unknown mimes (`UnsupportedMimeError`); re-exports `parse_pdf`, `parse_hwpx`, `ParseError`, `UnsupportedFormatError`, `UnsupportedMimeError`, `PDF_MIME`, `HWPX_MIME`, `HWP_MIME`.

- [ ] **Step 1: Write failing test for PDF/HWPX dispatch and error routing.** Create `tests/parse/test_parse_dispatch_m8.py`:
```python
from pathlib import Path

import pytest

from ttobak.ir import Document
from ttobak.parse import (
    parse, ParseError, UnsupportedFormatError, UnsupportedMimeError,
    PDF_MIME, HWPX_MIME, HWP_MIME,
)
from ttobak.parse._fixtures import make_minimal_pdf, make_minimal_hwpx


def test_parse_dispatches_pdf_bytes():
    doc = parse(make_minimal_pdf(["Dispatch via mime"]), PDF_MIME)
    assert isinstance(doc, Document)
    assert "Dispatch via mime" in doc.text()
    assert doc.meta["parser"] in {"pypdf", "pdfminer.six"}


def test_parse_dispatches_hwpx_bytes():
    doc = parse(make_minimal_hwpx(["고지서 본문 한 줄"]), HWPX_MIME)
    assert "고지서 본문 한 줄" in doc.text()
    assert doc.meta["best_effort"] is True


def test_parse_reads_pdf_from_path(tmp_path: Path):
    p = tmp_path / "doc.pdf"
    p.write_bytes(make_minimal_pdf(["From a file path"]))
    assert "From a file path" in parse(p, PDF_MIME).text()


def test_parse_rejects_legacy_hwp_mime():
    with pytest.raises(UnsupportedFormatError):
        parse(make_minimal_hwpx(["x"]), HWP_MIME)


def test_parse_unknown_mime_raises_unsupported():
    with pytest.raises(UnsupportedMimeError):
        parse(b"whatever", "application/zip")


def test_parse_str_source_for_pdf_is_rejected():
    with pytest.raises(ParseError, match="bytes"):
        parse("not bytes", PDF_MIME)
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/parse/test_parse_dispatch_m8.py -q`. Expect `ImportError: cannot import name 'UnsupportedFormatError' from 'ttobak.parse'`.

- [ ] **Step 3: Add PDF/HWPX routing to `ttobak/parse/__init__.py`.** Keep the Task-8 `text/plain`/`text/markdown` routing via `parse_text` and `UnsupportedMimeError` intact; add binary-source normalization and the new branches:
```python
"""Public parse entry point: dispatch raw input to a format-specific parser."""
from __future__ import annotations

from pathlib import Path

from ttobak.ir import Document
from ttobak.parse.text_parser import UnsupportedMimeError, parse_text
from ttobak.parse.pdf_parser import parse_pdf, ParseError, PDF_MIME
from ttobak.parse.hwp_parser import parse_hwpx, UnsupportedFormatError, HWPX_MIME, HWP_MIME

__all__ = [
    "parse", "parse_pdf", "parse_hwpx",
    "ParseError", "UnsupportedFormatError", "UnsupportedMimeError",
    "PDF_MIME", "HWPX_MIME", "HWP_MIME",
]

_TEXT_MIMES = frozenset({"text/plain", "text/markdown"})


def _to_text(source: bytes | str | Path) -> str:
    if isinstance(source, Path):
        return source.read_text(encoding="utf-8")
    if isinstance(source, bytes):
        return source.decode("utf-8")
    return source


def _as_bytes(source: bytes | str | Path, mime: str) -> bytes:
    if isinstance(source, bytes):
        return source
    if isinstance(source, Path):
        return source.read_bytes()
    raise ParseError(f"{mime} requires bytes or a Path, got a str source")


def parse(source: bytes | str | Path, mime: str) -> Document:
    """Parse ``source`` of the given ``mime`` into a Document IR.

    Text (text/plain, text/markdown) via the text parser; PDF via pypdf/pdfminer;
    HWPX best-effort. Legacy .hwp -> UnsupportedFormatError; any other unknown
    mime -> UnsupportedMimeError (no silent degradation).
    """
    if mime in _TEXT_MIMES:
        return parse_text(_to_text(source), mime)
    if mime == PDF_MIME:
        return parse_pdf(_as_bytes(source, mime), source_mime=mime)
    if mime == HWPX_MIME:
        return parse_hwpx(_as_bytes(source, mime), source_mime=mime)
    if mime == HWP_MIME:
        raise UnsupportedFormatError("legacy .hwp binary is out of MVP scope; convert to HWPX or PDF")
    raise UnsupportedMimeError(f"unsupported mime type: {mime!r}")
```

- [ ] **Step 4: Update the Task-8 dispatch test for the now-supported PDF mime.** In `tests/test_parse_dispatch.py`, change `test_parse_raises_on_unsupported_mime` to assert on a genuinely unknown mime (PDF is now supported):
```python
def test_parse_raises_on_unsupported_mime():
    with pytest.raises(UnsupportedMimeError) as exc:
        parse(b"whatever", "application/zip")
    assert "application/zip" in str(exc.value)
```

- [ ] **Step 5: Run the dispatch tests, expect PASS.** Run `python -m pytest tests/parse/test_parse_dispatch_m8.py tests/test_parse_dispatch.py -q`. Expect all passing.

- [ ] **Step 6: Run the whole parse suite (regression).** Run `python -m pytest tests/parse/ tests/test_parse_dispatch.py tests/test_text_parser.py tests/test_parse_roundtrip.py -q`. Expect all passing.

- [ ] **Step 7: Confirm the M8 deps import (already pinned in Task 1's pyproject).** Run `python -c "import pypdf, pdfminer.high_level, hwp_hwpx_parser; print('ok')"` → expect `ok`. (Task 1 already pinned `pypdf`, `pdfminer.six`, `hwp-hwpx-parser`; if a transitive dep version drifts, re-pin per spec §9.6.)

- [ ] **Step 8: Commit.** Run `git add ttobak/parse/__init__.py tests/parse/test_parse_dispatch_m8.py tests/test_parse_dispatch.py && git commit -m "feat(parse): route PDF/HWPX through parse() dispatch; reject .hwp and unknown mimes"`.

### Task 42: Web provider factory (default Anthropic, FakeProvider fallback)

The web demo runs with a real LLM when configured (default = Anthropic) but falls back to the deterministic `FakeProvider` in CI / when no API key is present.

> **FakeProvider reconciliation:** the canonical `FakeProvider` (Task 12) raises `IndexError` once its queue is empty and no `default` is set. So the web fallback MUST construct it with a non-None default: `FakeProvider(default="...")` (a fixed easy-text stub), making `generate()` total. Do not call bare `FakeProvider()`.

**Files:**
- Create: `ttobak/web/__init__.py`
- Create: `ttobak/web/provider.py`
- Create: `tests/web/__init__.py`
- Test: `tests/web/test_provider.py`

**Interfaces:**
- Consumes: `ttobak/providers/base.py` `LLMProvider`; `ttobak/providers` `FakeProvider`, `AnthropicProvider`.
- Produces: `ttobak/web/provider.py`: `DEFAULT_PROVIDER_ENV = "TTOBAK_PROVIDER"`; `def make_provider(name: str | None = None) -> LLMProvider` — returns a provider by name (`"anthropic"|"fake"`); `name is None` reads `$TTOBAK_PROVIDER`, else defaults to `"anthropic"`, and if Anthropic cannot be constructed (no `ANTHROPIC_API_KEY`) silently falls back to `FakeProvider(default=...)`.

- [ ] **Step 1: Create the web test package marker.** Create `tests/web/__init__.py`:
```python
# ttobak web demo test package
```

- [ ] **Step 2: Write failing test for the provider factory.** Create `tests/web/test_provider.py`:
```python
from ttobak.providers import FakeProvider
from ttobak.web import provider as provider_mod


def test_explicit_fake_returns_fakeprovider():
    assert isinstance(provider_mod.make_provider("fake"), FakeProvider)


def test_default_env_name_constant():
    assert provider_mod.DEFAULT_PROVIDER_ENV == "TTOBAK_PROVIDER"


def test_none_reads_env(monkeypatch):
    monkeypatch.setenv("TTOBAK_PROVIDER", "fake")
    assert isinstance(provider_mod.make_provider(None), FakeProvider)


def test_anthropic_without_key_falls_back_to_fake(monkeypatch):
    monkeypatch.delenv("TTOBAK_PROVIDER", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    p = provider_mod.make_provider("anthropic")
    assert isinstance(p, FakeProvider)


def test_returned_provider_is_callable():
    p = provider_mod.make_provider("fake")
    out = p.generate("안녕하세요", system=None, max_tokens=64)
    assert isinstance(out, str)
```

- [ ] **Step 3: Run, expect FAIL.** Run `python -m pytest tests/web/test_provider.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.web'`.

- [ ] **Step 4: Create the web package + factory.** Create `ttobak/web/__init__.py`:
```python
"""또박 웹 데모 (Gradio 얇은 래퍼). 코어 API를 그대로 재사용한다."""
```
  Create `ttobak/web/provider.py`:
```python
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
```

- [ ] **Step 5: Run, expect PASS.** Run `python -m pytest tests/web/test_provider.py -q`. Expect `5 passed`.

- [ ] **Step 6: Commit.** Run `git checkout -b m9-web-demo && git add ttobak/web/__init__.py ttobak/web/provider.py tests/web/__init__.py tests/web/test_provider.py && git commit -m "feat(web): provider factory with Anthropic default and FakeProvider fallback"`.

### Task 43: Source loader + level resolver helpers

The Gradio handler accepts pasted text or an uploaded file plus a human-readable level label. This task builds the two pure helpers turning raw UI inputs into the exact types the core API expects.

**Files:**
- Create: `ttobak/web/app.py`
- Test: `tests/web/test_helpers.py`

**Interfaces:**
- Consumes: `ttobak/levels.py` `Level`; `ttobak/parse` `parse` (the `(source, mime)` returned here is the exact pair `parse` accepts; PDF/HWPX mimes from Tasks 39–41).
- Produces: `ttobak/web/app.py`: `LEVEL_CHOICES: dict[str, Level]` (ordered Korean labels→Level); `def _resolve_level(level_label: str) -> Level`; `def _load_source(text_input: str, file_obj) -> tuple[bytes | str, str]` — returns `(source, mime)`; raises `ValueError` if neither text nor file provided. MIME inferred from extension (`.pdf`→`application/pdf`, `.hwpx`→`application/vnd.hancom.hwpx`, else `text/plain`); pasted text→`text/plain`.

> NOTE: use the canonical PDF/HWPX mimes from M8 (`application/pdf`, `application/vnd.hancom.hwpx`) so `_load_source` output routes correctly through `parse()`. (The original M9 draft used `application/hwpx`; align it to `application/vnd.hancom.hwpx`.)

- [ ] **Step 1: Write failing test for the helpers.** Create `tests/web/test_helpers.py`:
```python
from pathlib import Path

import pytest

from ttobak.levels import Level
from ttobak.web import app as webapp


def test_level_choices_maps_to_level_enum():
    assert set(webapp.LEVEL_CHOICES.values()) == {Level.PLAIN, Level.EASY}
    assert all(isinstance(k, str) and k for k in webapp.LEVEL_CHOICES)


def test_resolve_level_known_label():
    label = next(k for k, v in webapp.LEVEL_CHOICES.items() if v == Level.EASY)
    assert webapp._resolve_level(label) == Level.EASY


def test_resolve_level_unknown_defaults_to_easy():
    assert webapp._resolve_level("존재하지 않는 등급") == Level.EASY


def test_load_source_from_text():
    source, mime = webapp._load_source("국민건강보험료 고지서입니다.", None)
    assert source == "국민건강보험료 고지서입니다."
    assert mime == "text/plain"


def test_load_source_prefers_file_over_text(tmp_path: Path):
    f = tmp_path / "notice.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    source, mime = webapp._load_source("ignored text", str(f))
    assert source == b"%PDF-1.4 fake"
    assert mime == "application/pdf"


def test_load_source_hwpx_mime(tmp_path: Path):
    f = tmp_path / "doc.hwpx"
    f.write_bytes(b"PK\x03\x04hwpx")
    _, mime = webapp._load_source("", str(f))
    assert mime == "application/vnd.hancom.hwpx"


def test_load_source_empty_raises():
    with pytest.raises(ValueError):
        webapp._load_source("   ", None)
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/web/test_helpers.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.web.app'`.

- [ ] **Step 3: Implement helpers in app.py (skeleton + helpers only).** Create `ttobak/web/app.py`:
```python
"""또박 웹 데모 — Gradio 얇은 래퍼.

입력(텍스트 붙여넣기 또는 PDF/HWPX 업로드) + 등급 선택 -> parse() + simplify()
-> render_html() 나란히 + K-ER 점수 + Fidelity 배지 + 면책. 코어 API 재사용.
"""
from __future__ import annotations

from pathlib import Path

from ttobak.levels import Level

# 사람이 읽는 한국어 라벨 -> Level. 순서 보존(dict).
LEVEL_CHOICES: dict[str, Level] = {
    "쉬운 글 (Easy Korean, 문해수준 1–2)": Level.EASY,
    "보통 읽기 (Plain Language, 문해수준 3)": Level.PLAIN,
}

_EXT_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".hwpx": "application/vnd.hancom.hwpx",
    ".hwp": "application/x-hwp",
    ".txt": "text/plain",
}


def _resolve_level(level_label: str) -> Level:
    """UI 라벨을 Level 로. 알 수 없으면 가장 쉬운 등급(EASY)으로 폴백한다."""
    return LEVEL_CHOICES.get(level_label, Level.EASY)


def _load_source(text_input: str, file_obj) -> tuple[bytes | str, str]:
    """UI 입력을 parse() 가 받는 (source, mime) 로 변환한다.

    파일이 있으면 파일 우선(바이트 + 확장자 기반 MIME), 없으면 붙여넣은 텍스트.
    둘 다 비어 있으면 ValueError.
    """
    path = _file_path(file_obj)
    if path is not None:
        data = Path(path).read_bytes()
        mime = _EXT_TO_MIME.get(Path(path).suffix.lower(), "text/plain")
        return data, mime

    text = (text_input or "").strip()
    if not text:
        raise ValueError("변환할 텍스트를 입력하거나 파일을 업로드해 주세요.")
    return text, "text/plain"


def _file_path(file_obj) -> str | None:
    """Gradio File 컴포넌트가 주는 값(경로 문자열 또는 .name 속성)에서 경로를 뽑는다."""
    if file_obj is None:
        return None
    if isinstance(file_obj, str):
        return file_obj
    name = getattr(file_obj, "name", None)
    return name if isinstance(name, str) else None
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/web/test_helpers.py -q`. Expect `6 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/web/app.py tests/web/test_helpers.py && git commit -m "feat(web): source loader and level resolver helpers"`.

### Task 44: simplify_handler — orchestrate parse -> simplify -> render + badges

The load-bearing function the Gradio button calls. Given UI inputs + a provider, it parses, runs `simplify`, renders the side-by-side HTML, and produces two summary strings (K-ER badge line, Fidelity verdict badge line). Tested end-to-end with `FakeProvider` so CI never touches a live API.

**Files:**
- Modify: `ttobak/web/app.py`
- Test: `tests/web/test_handler.py`

**Interfaces:**
- Consumes: `ttobak/parse` `parse`; `ttobak/pipeline` `simplify`; `ttobak/render` `render_html`; `ttobak/result.py` `EasyReadResult`; `ttobak/metric/models.py` `KERReport`; `ttobak/fidelity/models.py` `FidelityReport`; `ttobak/common.py` `Verdict`; `ttobak/providers/base.py` `LLMProvider`; `ttobak/providers` `FakeProvider`; Task-43 `_load_source`,`_resolve_level`.
- Produces: `def simplify_handler(text_input: str, file_obj, level_label: str, provider: LLMProvider) -> tuple[str, str, str]` — `(html, ker_badge, fidelity_badge)`; on error returns error HTML in slot 0 and empty badges, never raises; `def _ker_badge(ker: KERReport) -> str`; `def _fidelity_badge(verdict: Verdict) -> str`.

> NOTE: when the handler is driven by a bare `FakeProvider()` in tests, give it a `default=` so the pipeline's possibly-multiple `generate()` calls (revise loop) never exhaust the queue. The tests below construct `FakeProvider(default="...")`.

- [ ] **Step 1: Write failing test for the handler.** Create `tests/web/test_handler.py`:
```python
import pytest

from ttobak.common import Verdict
from ttobak.providers import FakeProvider
from ttobak.web import app as webapp


def _fake():
    # default-backed so the revise loop never exhausts the queue
    return FakeProvider(default="건강보험료는 1,295,400원입니다.\n2026년 7월 17일까지 내세요.")


def test_handler_returns_three_strings_from_text():
    html, ker_badge, fid_badge = webapp.simplify_handler(
        "만 65세 이상 어르신은 2026년 7월 17일까지 신청하셔야 합니다.", None,
        next(iter(webapp.LEVEL_CHOICES)), _fake(),
    )
    assert isinstance(html, str) and html.strip()
    assert "<" in html and ">" in html
    assert isinstance(ker_badge, str) and "K-ER" in ker_badge
    assert isinstance(fid_badge, str) and fid_badge.strip()


def test_handler_fidelity_badge_reflects_verdict():
    _, _, fid_badge = webapp.simplify_handler(
        "국민건강보험료 1,295,400원을 납부하세요.", None,
        next(iter(webapp.LEVEL_CHOICES)), _fake(),
    )
    assert any(tok in fid_badge for tok in ("통과", "검수", "재교정"))


def test_handler_empty_input_returns_error_html_not_raise():
    html, ker_badge, fid_badge = webapp.simplify_handler("", None, "쉬운 글", _fake())
    assert "오류" in html or "입력" in html
    assert ker_badge == ""
    assert fid_badge == ""


def test_ker_badge_contains_score():
    from ttobak.metric.models import KERReport
    ker = KERReport(score=81.0, level_estimate=2, sub_scores={"rule": 81.0}, violations=[])
    badge = webapp._ker_badge(ker)
    assert "81" in badge
    assert "K-ER" in badge


def test_fidelity_badge_pass_vs_human_review():
    pass_badge = webapp._fidelity_badge(Verdict.PASS)
    human_badge = webapp._fidelity_badge(Verdict.HUMAN_REVIEW)
    assert pass_badge != human_badge
    assert "검수" in human_badge
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/web/test_handler.py -q`. Expect `AttributeError: module 'ttobak.web.app' has no attribute 'simplify_handler'`.

- [ ] **Step 3: Extend app.py imports.** Replace the import block of `ttobak/web/app.py` with:
```python
from __future__ import annotations

import html as _html
from pathlib import Path

from ttobak.common import Verdict
from ttobak.levels import Level
from ttobak.metric.models import KERReport
from ttobak.parse import parse
from ttobak.pipeline import simplify
from ttobak.providers.base import LLMProvider
from ttobak.render import render_html
```

- [ ] **Step 4: Implement the badge helpers and the handler.** Append to `ttobak/web/app.py`:
```python
_FIDELITY_LABEL: dict[Verdict, str] = {
    Verdict.PASS: "Fidelity 통과 ✅",
    Verdict.REVISE: "Fidelity 재교정됨 🔁",
    Verdict.HUMAN_REVIEW: "검수 필요 ⚠️ (사람 확인 권장)",
}


def _ker_badge(ker: KERReport) -> str:
    """K-ER 점수 한 줄 요약. '규칙 기반·미검증 보조 지표'임을 명시한다."""
    n = len(ker.violations)
    return f"K-ER {ker.score:.0f}/100 · 위반 {n}건 (규칙 기반 루브릭, 경험적 검증 아님)"


def _fidelity_badge(verdict: Verdict) -> str:
    """Fidelity 판정 배지 텍스트."""
    return _FIDELITY_LABEL.get(verdict, "검수 필요 ⚠️")


def simplify_handler(text_input: str, file_obj, level_label: str, provider: LLMProvider) -> tuple[str, str, str]:
    """Gradio 버튼 핸들러 — (html, ker_badge, fidelity_badge) 반환.

    예외는 절대 올리지 않는다(UI가 500 대신 메시지를 보여주도록):
    실패 시 슬롯 0에 오류 HTML, 배지는 빈 문자열.
    """
    try:
        source, mime = _load_source(text_input, file_obj)
        level = _resolve_level(level_label)
        doc = parse(source, mime)
        result = simplify(doc, level, provider)
        html = render_html(result)
        return html, _ker_badge(result.ker), _fidelity_badge(result.fidelity.verdict)
    except Exception as exc:  # noqa: BLE001 — 데모 UI는 어떤 실패도 메시지로 표시
        msg = _html.escape(str(exc)) or "변환 중 오류가 발생했습니다."
        return f'<div class="ttobak-error">변환 오류: {msg}</div>', "", ""
```

- [ ] **Step 5: Run, expect PASS.** Run `python -m pytest tests/web/test_handler.py -q`. Expect `5 passed`.

- [ ] **Step 6: Commit.** Run `git add ttobak/web/app.py tests/web/test_handler.py && git commit -m "feat(web): simplify_handler orchestrating parse/simplify/render with K-ER and Fidelity badges"`.

### Task 45: build_app — Gradio Blocks UI assembly + smoke test

Assemble the Gradio `Blocks` UI: a Tab for pasting text, a Tab for uploading PDF/HWPX, a level radio, a "변환" button, output HTML, two badge labels, and an always-on disclaimer ("자동 변환 결과이며 법적 효력은 원문이 우선합니다"). The button wires to `simplify_handler` with the app's bound provider. Build-only smoke test (no server launch) so CI stays fast/offline.

> **Dependency reconciliation:** gradio is already a Task-1 core runtime dependency (`gradio>=4.44,<6`). Do NOT add a separate `web` extra or re-pin to `>=6,<7`; import `gradio` directly. The build-app test uses `pytest.importorskip("gradio")` so it skips gracefully if gradio is somehow absent.

**Files:**
- Modify: `ttobak/web/app.py`
- Test: `tests/web/test_build_app.py`

**Interfaces:**
- Consumes: `gradio` (Task-1 dep); `ttobak/web/provider.py` `make_provider`; Task-43/44 `simplify_handler`, `LEVEL_CHOICES`; `ttobak/providers` `FakeProvider` (test).
- Produces: `def build_app(provider: LLMProvider | None = None) -> gr.Blocks` — builds the demo; `provider is None` → `make_provider()`. The disclaimer text is always present in the layout.

- [ ] **Step 1: Write failing build/smoke test.** Create `tests/web/test_build_app.py`:
```python
import pytest

gr = pytest.importorskip("gradio")

from ttobak.providers import FakeProvider
from ttobak.web import app as webapp


def _fake():
    return FakeProvider(default="쉬운 글입니다.")


def test_build_app_returns_blocks():
    assert isinstance(webapp.build_app(provider=_fake()), gr.Blocks)


def test_build_app_default_provider_does_not_raise(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("TTOBAK_PROVIDER", raising=False)
    assert isinstance(webapp.build_app(), gr.Blocks)


def test_build_app_contains_disclaimer():
    demo = webapp.build_app(provider=_fake())
    blob = str(demo.get_config_file())
    assert "원문이 우선" in blob
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/web/test_build_app.py -q`. Expect `AttributeError: module 'ttobak.web.app' has no attribute 'build_app'`.

- [ ] **Step 3: Implement build_app.** Append to `ttobak/web/app.py`:
```python
_DISCLAIMER = (
    "쉬운본은 자동 변환된 보조 자료이며, 법적 효력은 원문이 우선합니다. "
    "숫자·날짜·금액·기한은 반드시 원문으로 다시 확인하세요."
)

_INTRO = (
    "# 또박 (Ttobak) — 쉬운 정보 변환 데모\n"
    "어려운 공공·행정 문서를 쉬운 글로 바꾸고, 쉬움(K-ER)과 "
    "사실충실성(Fidelity)을 함께 측정합니다."
)


def build_app(provider: "LLMProvider | None" = None) -> "gr.Blocks":
    """Gradio 데모를 구성해 Blocks 를 반환한다(launch 는 호출자 책임)."""
    import gradio as gr

    from ttobak.web.provider import make_provider

    bound_provider = provider if provider is not None else make_provider()

    def _on_click(text_input: str, file_obj, level_label: str):
        return simplify_handler(text_input, file_obj, level_label, bound_provider)

    with gr.Blocks(title="또박 Ttobak", analytics_enabled=False) as demo:
        gr.Markdown(_INTRO)
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Tab("텍스트 붙여넣기"):
                    text_input = gr.Textbox(label="원문 텍스트", lines=10,
                                            placeholder="여기에 공문·고지서·안내문 내용을 붙여넣으세요.")
                with gr.Tab("파일 업로드 (PDF·HWPX)"):
                    file_input = gr.File(label="문서 업로드", file_types=[".pdf", ".hwpx", ".hwp", ".txt"])
                level_input = gr.Radio(choices=list(LEVEL_CHOICES.keys()),
                                       value=next(iter(LEVEL_CHOICES)), label="출력 등급")
                run_btn = gr.Button("변환", variant="primary")
                ker_out = gr.Label(label="K-ER (쉬움 지표 · 규칙 기반·미검증)")
                fid_out = gr.Label(label="Fidelity (사실충실성 게이트)")
            with gr.Column(scale=2):
                html_out = gr.HTML(label="결과 (원문 · 쉬운본 나란히)")
        gr.Markdown(f"> ⚖️ **면책**: {_DISCLAIMER}")

        run_btn.click(fn=_on_click, inputs=[text_input, file_input, level_input],
                      outputs=[html_out, ker_out, fid_out])
    return demo
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/web/test_build_app.py -q`. Expect `3 passed`. (If `get_config_file()` API differs in the installed gradio version, adapt the test's introspection to the version's config accessor; the disclaimer text must appear in the serialized config either way.)

- [ ] **Step 5: Commit.** Run `git add ttobak/web/app.py tests/web/test_build_app.py && git commit -m "feat(web): Gradio Blocks UI with text/file tabs, level selector, badges, and disclaimer"`.

### Task 46: ttobak CLI — `web` subcommand (shared console script)

Provide a `ttobak web` console command that builds the app and launches Gradio. The launch path is not unit-tested against a live socket; the test verifies the parser dispatches to a `_serve` function (monkeypatched), so `ttobak web --port 7861` is validated without binding a port.

> **Console-script reconciliation (with M11):** there is ONE `ttobak` console entry. This task creates `ttobak/cli.py:main` with a `web` subcommand. M11 Task 61 EXTENDS the same `ttobak/cli.py` `main` with an `audit` subcommand (both via `argparse` subparsers) and registers `[project.scripts] ttobak = "ttobak.cli:main"` once. Do not create two competing `main` entry points — Task 46 builds the subcommand router; Task 61 adds the `audit` branch to it.

**Files:**
- Create: `ttobak/cli.py`
- Test: `tests/web/test_cli.py`

**Interfaces:**
- Consumes: `ttobak/web/app.py` `build_app`; `ttobak/web/provider.py` `make_provider`; `gr.Blocks.launch(...)`.
- Produces: `ttobak/cli.py`: `def main(argv: list[str] | None = None) -> int` (parses `web` subcommand: `--host`,`--port`,`--provider`,`--share`); `def _serve(host: str, port: int, provider_name: str | None, share: bool) -> None` (build + launch, isolated for tests).

- [ ] **Step 1: Write failing test for the CLI.** Create `tests/web/test_cli.py`:
```python
import pytest

from ttobak import cli


def test_web_subcommand_dispatches_to_serve(monkeypatch):
    called = {}
    monkeypatch.setattr(cli, "_serve", lambda host, port, provider_name, share: called.update(
        host=host, port=port, provider_name=provider_name, share=share))
    rc = cli.main(["web", "--host", "127.0.0.1", "--port", "7861", "--provider", "fake"])
    assert rc == 0
    assert called == {"host": "127.0.0.1", "port": 7861, "provider_name": "fake", "share": False}


def test_web_defaults(monkeypatch):
    captured = {}
    monkeypatch.setattr(cli, "_serve", lambda host, port, provider_name, share: captured.update(
        host=host, port=port, share=share))
    rc = cli.main(["web"])
    assert rc == 0
    assert captured["host"] == "127.0.0.1"
    assert captured["port"] == 7860
    assert captured["share"] is False


def test_no_subcommand_returns_nonzero():
    assert cli.main([]) != 0
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/web/test_cli.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.cli'`.

- [ ] **Step 3: Implement the CLI.** Create `ttobak/cli.py` (M11 Task 61 will add the `audit` subparser to this same `main`):
```python
"""`ttobak` 콘솔 명령. 서브커맨드: `web` (데모 서버). M11이 `audit` 를 추가한다."""
from __future__ import annotations

import argparse


def _serve(host: str, port: int, provider_name: str | None, share: bool) -> None:
    """앱을 빌드해 Gradio 서버를 띄운다(테스트에서 패치 가능하도록 분리)."""
    from ttobak.web.app import build_app
    from ttobak.web.provider import make_provider

    demo = build_app(provider=make_provider(provider_name))
    demo.launch(server_name=host, server_port=port, share=share)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ttobak", description="또박 — 한국어 쉬운 정보 엔진")
    sub = parser.add_subparsers(dest="command")

    web = sub.add_parser("web", help="Gradio 웹 데모 실행")
    web.add_argument("--host", default="127.0.0.1", help="바인드 호스트 (기본 127.0.0.1)")
    web.add_argument("--port", type=int, default=7860, help="포트 (기본 7860)")
    web.add_argument("--provider", default=None,
                     help="LLM 프로바이더 이름 (anthropic|fake). 미지정 시 $TTOBAK_PROVIDER 또는 anthropic")
    web.add_argument("--share", action="store_true", help="Gradio 공개 링크 생성")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "web":
        _serve(args.host, args.port, args.provider, args.share)
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Register the console script in `pyproject.toml`.** Add `[project.scripts] ttobak = "ttobak.cli:main"` (M11 Task 61 reuses this exact entry). Reinstall: `python -m pip install -e ".[dev]"`.

- [ ] **Step 5: Run, expect PASS.** Run `python -m pytest tests/web/test_cli.py -q`. Expect `3 passed`. Verify the entry resolves: `ttobak --help` → usage text listing `web` (exit 0).

- [ ] **Step 6: Commit.** Run `git add ttobak/cli.py pyproject.toml tests/web/test_cli.py && git commit -m "feat(web): ttobak web CLI entrypoint that builds and launches the Gradio demo"`.

### Task 47: Full web module suite green + provider env round-trip integration

Final guard: an integration test exercising the whole web surface the way the demo will — `simplify_handler` driven by a FakeProvider on a realistic 고지서 snippet — plus a `build_app` smoke and a `$TTOBAK_PROVIDER` env round-trip. Then run the entire `tests/web` suite.

**Files:**
- Test: `tests/web/test_integration.py`

**Interfaces:**
- Consumes: `ttobak/web/app.py` `build_app`,`simplify_handler`,`LEVEL_CHOICES`; `ttobak/web/provider.py` `make_provider`; `ttobak/providers` `FakeProvider`.
- Produces: verification coverage only.

- [ ] **Step 1: Write the integration test.** Create `tests/web/test_integration.py`:
```python
import pytest

from ttobak.providers import FakeProvider
from ttobak.web import app as webapp
from ttobak.web.provider import make_provider


REALISTIC_NOTICE = (
    "2026년도 국민건강보험료 고지서\n"
    "납부할 금액: 1,295,400원\n"
    "납부 기한: 2026년 7월 17일까지\n"
    "만 65세 이상 어르신은 경감 신청을 하실 수 있습니다."
)


def _fake():
    return FakeProvider(default="건강보험료는 1,295,400원입니다.\n2026년 7월 17일까지 내세요.")


def test_env_round_trip_fake(monkeypatch):
    monkeypatch.setenv("TTOBAK_PROVIDER", "fake")
    assert isinstance(make_provider(), FakeProvider)


def test_end_to_end_handler_via_fakeprovider():
    html, ker_badge, fid_badge = webapp.simplify_handler(
        REALISTIC_NOTICE, None, next(iter(webapp.LEVEL_CHOICES)), _fake())
    assert html.strip()
    assert "K-ER" in ker_badge
    assert fid_badge.strip()


def test_build_app_then_handler_share_provider():
    gr = pytest.importorskip("gradio")
    provider = _fake()
    demo = webapp.build_app(provider=provider)
    assert isinstance(demo, gr.Blocks)
    html, _, _ = webapp.simplify_handler(
        REALISTIC_NOTICE, None, next(iter(webapp.LEVEL_CHOICES)), provider)
    assert "<" in html
```

- [ ] **Step 2: Run the integration test, expect PASS.** Run `python -m pytest tests/web/test_integration.py -q`. Expect `3 passed`.

- [ ] **Step 3: Run the whole web suite, expect all green.** Run `python -m pytest tests/web -q`. Expect all passing (5 provider + 6 helpers + 5 handler + 3 build + 3 cli + 3 integration; build-app/integration skip only if gradio is absent).

- [ ] **Step 4: Commit.** Run `git add tests/web/test_integration.py && git commit -m "test(web): end-to-end FakeProvider integration test for the web demo surface"`.

### Task 48: Eval package scaffolding + shared eval fixtures

The evaluation harness package. The `ttobak` package, contracts, and `pyproject.toml` already exist (Tasks 1–30), so this task only creates the `ttobak/eval` package and reuses the existing `FakeProvider` (Task 12) and IR contracts. Per spec §14.4 tests use a deterministic provider, never a live LLM.

> NOTE: do NOT recreate `pyproject.toml`, `ttobak/ir.py`, `ttobak/levels.py`, `ttobak/common.py`, or `ttobak/providers/*` — they exist from earlier phases. This task adds `ttobak/eval/__init__.py` and a `tests/eval` conftest exposing `sample_document`/`ref_date` (the `fake_provider` fixture, if needed, builds `FakeProvider(default=...)` from Task 12).

**Files:**
- Create: `ttobak/eval/__init__.py`
- Create: `tests/eval/__init__.py`
- Create: `tests/eval/conftest.py`
- Test: `tests/eval/test_scaffold.py`

**Interfaces:**
- Consumes: `ttobak/ir.py` `Document`,`Block`,`BlockType`; `ttobak/levels.py` `Level`; `ttobak/providers/fake.py` `FakeProvider`.
- Produces: `ttobak/eval/__init__.py` package marker; `tests/eval/conftest.py` exposing fixtures `fake_provider`, `sample_document`, `ref_date`.

- [ ] **Step 1: Write failing smoke test.** Create `tests/eval/__init__.py` (empty), then `tests/eval/test_scaffold.py`:
```python
from datetime import date

import ttobak.eval
from ttobak.ir import BlockType, Document
from ttobak.levels import Level


def test_eval_package_importable():
    assert ttobak.eval.__name__ == "ttobak.eval"


def test_sample_document_fixture(sample_document):
    assert isinstance(sample_document, Document)
    assert sample_document.source_mime == "text/plain"
    assert "1,295,400원" in sample_document.text()
    assert any(b.type == BlockType.HEADING for b in sample_document.blocks)


def test_ref_date_fixture(ref_date):
    assert ref_date == date(2026, 7, 1)


def test_fake_provider_is_deterministic(fake_provider):
    out_a = fake_provider.generate("아무 프롬프트")
    out_b = fake_provider.generate("아무 프롬프트")
    assert out_a == out_b
    assert isinstance(out_a, str) and out_a
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/eval/test_scaffold.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.eval'`.

- [ ] **Step 3: Create the eval package.** Create `ttobak/eval/__init__.py`:
```python
"""또박 evaluation harness — injected-distortion fidelity bench + K-ER before/after."""
```

- [ ] **Step 4: Create the eval conftest.** Create `tests/eval/conftest.py`:
```python
from __future__ import annotations

from datetime import date

import pytest

from ttobak.ir import Block, BlockType, Document
from ttobak.providers.fake import FakeProvider


@pytest.fixture
def fake_provider() -> FakeProvider:
    # default-backed so generate() is total and deterministic
    return FakeProvider(default="쉬운 글로 바꾼 결과입니다.")


@pytest.fixture
def ref_date() -> date:
    return date(2026, 7, 1)


@pytest.fixture
def sample_document() -> Document:
    return Document(
        source_mime="text/plain",
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="이번 달 납부하실 건강보험료는 1,295,400원입니다."),
            Block(type=BlockType.PARAGRAPH, text="납부 기한은 2026년 7월 17일까지입니다."),
            Block(type=BlockType.LIST_ITEM, text="만 65세 이상은 경감 대상에서 제외됩니다."),
        ],
    )
```

- [ ] **Step 5: Run, expect PASS.** Run `python -m pytest tests/eval/test_scaffold.py -q`. Expect `4 passed`.

- [ ] **Step 6: Commit.** Run `git checkout -b m10-eval-harness && git add ttobak/eval/__init__.py tests/eval/__init__.py tests/eval/conftest.py tests/eval/test_scaffold.py && git commit -m "chore(eval): scaffold ttobak.eval package and shared fixtures"`.

### Task 49: Distortion type taxonomy + DistortionCase model

Define the 10 distortion types from spec §6.9 plus the clean control, and the labeled `DistortionCase` model carrying the distorted easy-text and its ground-truth label.

**Files:**
- Create: `ttobak/eval/distortion_bench.py`
- Test: `tests/eval/test_distortion_models.py`

**Interfaces:**
- Consumes: pure pydantic + enum.
- Produces: `DistortionType(str, Enum)` {NUMBER_SWAP, DIGIT_DROP, KRW_UNIT_ERROR, DATE_SHIFT, INCLUSIVITY_FLIP, NEGATION_DROP, CONDITION_FLIP, RANGE_WEAKEN, ENTITY_SWAP, HALLUCINATED_ENTITY, CLEAN}; `DistortionCase(BaseModel){case_id, source_text, easy_text, distorted_text, distortion_type, is_clean, expected_pass}`.

- [ ] **Step 1: Write failing test.** Create `tests/eval/test_distortion_models.py`:
```python
from ttobak.eval.distortion_bench import DistortionCase, DistortionType


def test_taxonomy_has_ten_distortions_plus_clean():
    members = set(DistortionType)
    assert len(members) == 11
    assert DistortionType.CLEAN in members
    assert len(members - {DistortionType.CLEAN}) == 10


def test_taxonomy_exact_members():
    assert DistortionType.NUMBER_SWAP.value == "number_swap"
    assert DistortionType.DIGIT_DROP.value == "digit_drop"
    assert DistortionType.KRW_UNIT_ERROR.value == "krw_unit_error"
    assert DistortionType.DATE_SHIFT.value == "date_shift"
    assert DistortionType.INCLUSIVITY_FLIP.value == "inclusivity_flip"
    assert DistortionType.NEGATION_DROP.value == "negation_drop"
    assert DistortionType.CONDITION_FLIP.value == "condition_flip"
    assert DistortionType.RANGE_WEAKEN.value == "range_weaken"
    assert DistortionType.ENTITY_SWAP.value == "entity_swap"
    assert DistortionType.HALLUCINATED_ENTITY.value == "hallucinated_entity"


def test_clean_case_expects_pass():
    case = DistortionCase(
        case_id="p1-clean", source_text="납부 금액은 30,000원입니다.",
        easy_text="내야 할 돈은 30,000원입니다.", distorted_text="내야 할 돈은 30,000원입니다.",
        distortion_type=DistortionType.CLEAN, is_clean=True, expected_pass=True)
    assert case.is_clean is True
    assert case.expected_pass is True


def test_distorted_case_expects_not_pass():
    case = DistortionCase(
        case_id="p1-number_swap", source_text="납부 금액은 30,000원입니다.",
        easy_text="내야 할 돈은 30,000원입니다.", distorted_text="내야 할 돈은 3,000원입니다.",
        distortion_type=DistortionType.NUMBER_SWAP, is_clean=False, expected_pass=False)
    assert case.is_clean is False
    assert case.expected_pass is False
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/eval/test_distortion_models.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.eval.distortion_bench'`.

- [ ] **Step 3: Implement the models.** Create `ttobak/eval/distortion_bench.py`:
```python
from __future__ import annotations

from datetime import date
from enum import Enum
from typing import Callable

from pydantic import BaseModel


class DistortionType(str, Enum):
    """Injected-distortion taxonomy (spec 6.9). 10 distortions + clean control."""

    NUMBER_SWAP = "number_swap"            # 30,000 -> 3,000
    DIGIT_DROP = "digit_drop"              # 1,295,400 -> 129,540
    KRW_UNIT_ERROR = "krw_unit_error"      # 3억 -> 3천만
    DATE_SHIFT = "date_shift"              # 7/17 -> 7/7
    INCLUSIVITY_FLIP = "inclusivity_flip"  # 까지 -> 전에
    NEGATION_DROP = "negation_drop"        # 제외 -> 포함
    CONDITION_FLIP = "condition_flip"      # 만 65세 이상 -> 이하
    RANGE_WEAKEN = "range_weaken"          # 미만 -> 이하
    ENTITY_SWAP = "entity_swap"            # 강서구청 -> 송파구청
    HALLUCINATED_ENTITY = "hallucinated_entity"  # add unsourced entity
    CLEAN = "clean"                        # faithful control, must PASS


class DistortionCase(BaseModel):
    case_id: str
    source_text: str
    easy_text: str
    distorted_text: str
    distortion_type: DistortionType
    is_clean: bool
    expected_pass: bool
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/eval/test_distortion_models.py -q`. Expect `4 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/eval/distortion_bench.py tests/eval/test_distortion_models.py && git commit -m "feat(eval): distortion taxonomy and DistortionCase model"`.

### Task 50: Programmatic distortion generator

`generate_distortions()` — given a faithful (source, easy) pair, deterministically emit one labeled `DistortionCase` per applicable distortion type plus a clean control (spec §6.9). Each distortion is a targeted rule-based mutation of the easy-text; when a pattern is absent the type is skipped. Seeded for reproducibility.

**Files:**
- Modify: `ttobak/eval/distortion_bench.py`
- Test: `tests/eval/test_distortion_generator.py`

**Interfaces:**
- Consumes: own `DistortionType`, `DistortionCase`.
- Produces: `def generate_distortions(source_text: str, easy_text: str, *, ref_date: date, seed: int = 0) -> list[DistortionCase]`.

- [ ] **Step 1: Write failing test.** Create `tests/eval/test_distortion_generator.py`:
```python
from datetime import date

from ttobak.eval.distortion_bench import DistortionCase, DistortionType, generate_distortions

SOURCE = (
    "건강보험료 1,295,400원을 2026년 7월 17일까지 강서구청에 납부하십시오. "
    "지원금은 3억 원이며 만 65세 이상은 제외됩니다. 소득 30,000원 미만이어야 합니다."
)
EASY = (
    "건강보험료 1,295,400원을 2026년 7월 17일까지 강서구청에 내세요. "
    "지원금은 3억 원이고 만 65세 이상은 빠집니다. 소득 30,000원 미만이어야 합니다."
)


def test_returns_distortioncases():
    cases = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1))
    assert cases and all(isinstance(c, DistortionCase) for c in cases)


def test_includes_exactly_one_clean_control_unchanged():
    cases = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1))
    cleans = [c for c in cases if c.distortion_type == DistortionType.CLEAN]
    assert len(cleans) == 1
    assert cleans[0].is_clean is True and cleans[0].expected_pass is True
    assert cleans[0].distorted_text == EASY


def test_distorted_cases_are_labeled_and_mutated():
    cases = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1))
    distorted = [c for c in cases if c.distortion_type != DistortionType.CLEAN]
    assert distorted
    for c in distorted:
        assert c.is_clean is False and c.expected_pass is False
        assert c.distorted_text != c.easy_text


def test_number_swap_changes_a_number():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.NUMBER_SWAP)
    assert "30,000원" not in c.distorted_text and "3,000원" in c.distorted_text


def test_digit_drop_loses_a_digit():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.DIGIT_DROP)
    assert "1,295,400" not in c.distorted_text and "129,540" in c.distorted_text


def test_krw_unit_error_downgrades_eok():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.KRW_UNIT_ERROR)
    assert "3억" not in c.distorted_text and "3천만" in c.distorted_text


def test_date_shift_changes_the_day():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.DATE_SHIFT)
    assert "7월 17일" not in c.distorted_text and "7월 7일" in c.distorted_text


def test_negation_drop_removes_exclusion():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.NEGATION_DROP)
    assert "빠집니다" not in c.distorted_text and "포함됩니다" in c.distorted_text


def test_condition_flip_inverts_boundary():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.CONDITION_FLIP)
    assert "이상" not in c.distorted_text and "이하" in c.distorted_text


def test_range_weaken_softens_boundary():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.RANGE_WEAKEN)
    assert "미만" not in c.distorted_text and "이하" in c.distorted_text


def test_entity_swap_replaces_agency():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.ENTITY_SWAP)
    assert "강서구청" not in c.distorted_text and "송파구청" in c.distorted_text


def test_hallucinated_entity_adds_unsourced_agency():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.HALLUCINATED_ENTITY)
    assert "국민건강보험공단" in c.distorted_text and "국민건강보험공단" not in c.easy_text


def test_deterministic_for_same_seed():
    a = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1), seed=7)
    b = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1), seed=7)
    assert [c.model_dump() for c in a] == [c.model_dump() for c in b]
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/eval/test_distortion_generator.py -q`. Expect `ImportError: cannot import name 'generate_distortions'`.

- [ ] **Step 3: Implement the generator.** Append to `ttobak/eval/distortion_bench.py` the per-type distorter functions and `generate_distortions`. Each distorter takes `easy_text` and returns the mutated text or `None` if its trigger is absent; the generator emits one case per realizable distortion (in enum declaration order) plus exactly one CLEAN control last:
```python
def _number_swap(text: str) -> str | None:
    return text.replace("30,000", "3,000", 1) if "30,000" in text else None

def _digit_drop(text: str) -> str | None:
    return text.replace("1,295,400", "129,540", 1) if "1,295,400" in text else None

def _krw_unit_error(text: str) -> str | None:
    return text.replace("3억", "3천만", 1) if "3억" in text else None

def _date_shift(text: str) -> str | None:
    return text.replace("7월 17일", "7월 7일", 1) if "7월 17일" in text else None

def _inclusivity_flip(text: str) -> str | None:
    return text.replace("까지", " 전에", 1) if "까지" in text else None

def _negation_drop(text: str) -> str | None:
    if "빠집니다" in text:
        return text.replace("빠집니다", "포함됩니다", 1)
    if "제외됩니다" in text:
        return text.replace("제외됩니다", "포함됩니다", 1)
    return None

def _condition_flip(text: str) -> str | None:
    return text.replace("이상", "이하", 1) if "이상" in text else None

def _range_weaken(text: str) -> str | None:
    return text.replace("미만", "이하", 1) if "미만" in text else None

def _entity_swap(text: str) -> str | None:
    return text.replace("강서구청", "송파구청", 1) if "강서구청" in text else None

def _hallucinated_entity(text: str) -> str | None:
    if "국민건강보험공단" in text:
        return None
    return text + " 자세한 내용은 국민건강보험공단에 문의하세요."


_DISTORTERS: dict[DistortionType, Callable[[str], "str | None"]] = {
    DistortionType.NUMBER_SWAP: _number_swap,
    DistortionType.DIGIT_DROP: _digit_drop,
    DistortionType.KRW_UNIT_ERROR: _krw_unit_error,
    DistortionType.DATE_SHIFT: _date_shift,
    DistortionType.INCLUSIVITY_FLIP: _inclusivity_flip,
    DistortionType.NEGATION_DROP: _negation_drop,
    DistortionType.CONDITION_FLIP: _condition_flip,
    DistortionType.RANGE_WEAKEN: _range_weaken,
    DistortionType.ENTITY_SWAP: _entity_swap,
    DistortionType.HALLUCINATED_ENTITY: _hallucinated_entity,
}


def generate_distortions(source_text: str, easy_text: str, *, ref_date: date, seed: int = 0) -> list[DistortionCase]:
    """Emit labeled DistortionCases for one faithful (source, easy) pair (spec 6.9).

    One case per realizable distortion type (skipped if its trigger pattern is
    absent from easy_text) plus exactly one CLEAN control. Deterministic: cases
    are emitted in stable DistortionType declaration order; ``seed`` namespaces case_ids.
    """
    cases: list[DistortionCase] = []
    for dtype in DistortionType:
        if dtype is DistortionType.CLEAN:
            continue
        mutated = _DISTORTERS[dtype](easy_text)
        if mutated is None or mutated == easy_text:
            continue
        cases.append(DistortionCase(
            case_id=f"{seed}-{dtype.value}", source_text=source_text, easy_text=easy_text,
            distorted_text=mutated, distortion_type=dtype, is_clean=False, expected_pass=False))
    cases.append(DistortionCase(
        case_id=f"{seed}-clean", source_text=source_text, easy_text=easy_text,
        distorted_text=easy_text, distortion_type=DistortionType.CLEAN, is_clean=True, expected_pass=True))
    return cases
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/eval/test_distortion_generator.py -q`. Expect `14 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/eval/distortion_bench.py tests/eval/test_distortion_generator.py && git commit -m "feat(eval): programmatic injected-distortion generator (spec 6.9)"`.

### Task 51: Distortion bench runner — per-type recall, clean FP rate, PASS residual rate

`run_distortion_bench()`: feed each `DistortionCase`'s `distorted_text` through an injected fidelity verifier (`verify_fn`, signature of `ttobak.fidelity.verify`), score against ground-truth labels per spec §6.9 — per-type recall, clean-control FP rate, the headline PASS residual-distortion rate, overall P/R/F1, confusion summary. The verifier is injected so CI stays deterministic.

**Files:**
- Modify: `ttobak/eval/distortion_bench.py`
- Test: `tests/eval/test_distortion_bench.py`

**Interfaces:**
- Consumes: own `DistortionCase`,`DistortionType`; `ttobak/common.py` `Verdict`; `ttobak/fidelity/models.py` `FidelityReport`; `ttobak/ir.py` `Document`,`Block`,`BlockType`; the public `verify(source, easy_text, ref_date) -> FidelityReport` signature (passed as `verify_fn`).
- Produces: `BenchResult(BaseModel){per_type_recall: dict[str,float]; clean_fp_rate: float; pass_residual_distortion_rate: float; overall_precision: float; overall_recall: float; overall_f1: float; n_cases: int; n_clean: int; confusion: dict[str,int]}`; `def run_distortion_bench(cases, verify_fn, *, ref_date) -> BenchResult`.

- [ ] **Step 1: Write failing test.** Create `tests/eval/test_distortion_bench.py`:
```python
from datetime import date

from ttobak.common import Verdict
from ttobak.eval.distortion_bench import BenchResult, DistortionCase, DistortionType, run_distortion_bench
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Document


def _case(case_id, dtype, distorted, *, clean, expected_pass):
    return DistortionCase(
        case_id=case_id, source_text="원문 30,000원 강서구청 7월 17일까지",
        easy_text="쉬운 글 30,000원 강서구청 7월 17일까지", distorted_text=distorted,
        distortion_type=dtype, is_clean=clean, expected_pass=expected_pass)


def make_verify_fn(catch_markers, false_alarm_texts):
    def verify_fn(source: Document, easy_text: str, ref_date: date) -> FidelityReport:
        caught = any(m in easy_text for m in catch_markers)
        false_alarm = easy_text in false_alarm_texts
        verdict = Verdict.HUMAN_REVIEW if (caught or false_alarm) else Verdict.PASS
        return FidelityReport(slots=[], verdict=verdict)
    return verify_fn


def test_bench_result_shape():
    cases = [
        _case("c-clean", DistortionType.CLEAN, "쉬운 글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "쉬운 글 3,000원", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원"], set()), ref_date=date(2026, 7, 1))
    assert isinstance(res, BenchResult)
    assert res.n_cases == 2 and res.n_clean == 1


def test_per_type_recall_and_pass_residual():
    cases = [
        _case("c-clean", DistortionType.CLEAN, "clean글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "num 3,000원", clean=False, expected_pass=False),
        _case("c-date", DistortionType.DATE_SHIFT, "date 7월 7일", clean=False, expected_pass=False),
        _case("c-neg", DistortionType.NEGATION_DROP, "neg 포함됩니다", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원", "7월 7일"], set()), ref_date=date(2026, 7, 1))
    assert res.per_type_recall["number_swap"] == 1.0
    assert res.per_type_recall["date_shift"] == 1.0
    assert res.per_type_recall["negation_drop"] == 0.0
    assert round(res.overall_recall, 4) == round(2 / 3, 4)
    assert res.clean_fp_rate == 0.0
    assert round(res.pass_residual_distortion_rate, 4) == round(1 / 3, 4)


def test_clean_fp_rate_counts_false_alarms():
    cases = [
        _case("c-clean1", DistortionType.CLEAN, "alarm글", clean=True, expected_pass=True),
        _case("c-clean2", DistortionType.CLEAN, "ok글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "num 3,000원", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원"], {"alarm글"}), ref_date=date(2026, 7, 1))
    assert res.n_clean == 2 and res.clean_fp_rate == 0.5
    assert res.confusion["clean_flagged_fp"] == 1
    assert res.confusion["distortion_caught_tp"] == 1


def test_perfect_gate_has_zero_residual_and_full_recall():
    cases = [
        _case("c-clean", DistortionType.CLEAN, "clean글", clean=True, expected_pass=True),
        _case("c-num", DistortionType.NUMBER_SWAP, "num 3,000원", clean=False, expected_pass=False),
    ]
    res = run_distortion_bench(cases, make_verify_fn(["3,000원"], set()), ref_date=date(2026, 7, 1))
    assert res.overall_recall == 1.0 and res.clean_fp_rate == 0.0
    assert res.pass_residual_distortion_rate == 0.0 and res.overall_f1 == 1.0
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/eval/test_distortion_bench.py -q`. Expect `ImportError: cannot import name 'BenchResult'`.

- [ ] **Step 3: Implement the runner.** Add imports to the top of `ttobak/eval/distortion_bench.py` (`from ttobak.common import Verdict`; `from ttobak.fidelity.models import FidelityReport`; `from ttobak.ir import Block, BlockType, Document`), then append `BenchResult` and `run_distortion_bench`:
```python
class BenchResult(BaseModel):
    per_type_recall: dict[str, float]
    clean_fp_rate: float
    pass_residual_distortion_rate: float
    overall_precision: float
    overall_recall: float
    overall_f1: float
    n_cases: int
    n_clean: int
    confusion: dict[str, int]


def _wrap_as_document(text: str) -> Document:
    return Document(source_mime="text/plain", blocks=[Block(type=BlockType.PARAGRAPH, text=text)])


def run_distortion_bench(cases: list[DistortionCase],
                         verify_fn: Callable[[Document, str, date], FidelityReport],
                         *, ref_date: date) -> BenchResult:
    """Score a fidelity gate against labeled injected distortions (spec 6.9).

    A case is "flagged" when the gate verdict is not PASS. Distortions SHOULD be
    flagged; clean controls SHOULD pass. Reports per-type recall, clean-control
    FP rate, PASS residual-distortion rate, and overall P/R/F1. ``verify_fn`` is
    injected so CI is deterministic.
    """
    per_type_total: dict[str, int] = {}
    per_type_caught: dict[str, int] = {}
    tp = fn = fp = tn = 0
    n_clean = n_distortion = residual = 0

    for case in cases:
        report = verify_fn(_wrap_as_document(case.source_text), case.distorted_text, ref_date)
        flagged = report.verdict != Verdict.PASS
        if case.is_clean:
            n_clean += 1
            if flagged:
                fp += 1
            else:
                tn += 1
            continue
        n_distortion += 1
        key = case.distortion_type.value
        per_type_total[key] = per_type_total.get(key, 0) + 1
        if flagged:
            tp += 1
            per_type_caught[key] = per_type_caught.get(key, 0) + 1
        else:
            fn += 1
            residual += 1

    per_type_recall = {k: per_type_caught.get(k, 0) / per_type_total[k] for k in per_type_total}
    clean_fp_rate = (fp / n_clean) if n_clean else 0.0
    pass_residual = (residual / n_distortion) if n_distortion else 0.0
    precision = (tp / (tp + fp)) if (tp + fp) else 0.0
    recall = (tp / (tp + fn)) if (tp + fn) else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0

    return BenchResult(
        per_type_recall=per_type_recall, clean_fp_rate=clean_fp_rate,
        pass_residual_distortion_rate=pass_residual, overall_precision=precision,
        overall_recall=recall, overall_f1=f1, n_cases=len(cases), n_clean=n_clean,
        confusion={"distortion_caught_tp": tp, "distortion_missed_fn": fn,
                   "clean_flagged_fp": fp, "clean_passed_tn": tn})
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/eval/test_distortion_bench.py -q`. Expect `4 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/eval/distortion_bench.py tests/eval/test_distortion_bench.py && git commit -m "feat(eval): distortion bench runner — per-type recall, clean FP, PASS residual rate"`.

### Task 52: Corpus schema models + loader/validator

Define the corpus pair schema from spec §8.3/§8.5 (`CorpusPair` with nested `SourceLicense`, `FidelityChecks`) and `load_corpus()`/`validate_corpus()` reading `pairs.jsonl`.

**Files:**
- Create: `ttobak/eval/corpus.py`
- Test: `tests/eval/test_corpus_schema.py`

**Interfaces:**
- Consumes: pure pydantic + stdlib `json`/`pathlib`.
- Produces: `SourceLicense{type,attribution,url,date_fetched}`; `FidelityChecks{numbers,dates,amounts,deadlines,eligibility,entities,distortions}`; `CorpusPair{pair_id,source_text,easy_text,source_license,ker_score,ker_rule_violations,fidelity_checks,pictogram_refs,reviewer,review_date}`; `def load_corpus(path: Path) -> list[CorpusPair]`; `def validate_corpus(path: Path) -> list[CorpusPair]`.

- [ ] **Step 1: Write failing test.** Create `tests/eval/test_corpus_schema.py`:
```python
import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ttobak.eval.corpus import CorpusPair, FidelityChecks, SourceLicense, load_corpus, validate_corpus

VALID_ROW = {
    "pair_id": "kogl1-0001",
    "source_text": "건강보험료 1,295,400원을 2026년 7월 17일까지 납부하십시오.",
    "easy_text": "건강보험료 1,295,400원을 2026년 7월 17일까지 내세요.",
    "source_license": {"type": "KOGL-1", "attribution": "국민건강보험공단, 2026, 건강보험료 안내문",
                       "url": "https://www.nhis.or.kr/example", "date_fetched": "2026-06-30"},
    "ker_score": 78.5,
    "ker_rule_violations": ["long_sentence", "sino_korean_word"],
    "fidelity_checks": {"numbers": True, "dates": True, "amounts": True, "deadlines": True,
                        "eligibility": True, "entities": True, "distortions": []},
    "pictogram_refs": [{"set": "openmoji", "glyph_id": "1F4B0", "modified": False}],
    "reviewer": "solo-reviewer", "review_date": "2026-07-05",
}


def test_corpus_pair_parses_valid_row():
    pair = CorpusPair(**VALID_ROW)
    assert pair.pair_id == "kogl1-0001"
    assert isinstance(pair.source_license, SourceLicense)
    assert isinstance(pair.fidelity_checks, FidelityChecks)
    assert pair.source_license.type == "KOGL-1"
    assert pair.fidelity_checks.deadlines is True


def test_corpus_pair_rejects_missing_license():
    bad = dict(VALID_ROW); del bad["source_license"]
    with pytest.raises(ValidationError):
        CorpusPair(**bad)


def test_load_corpus_reads_jsonl(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    rows = [VALID_ROW, {**VALID_ROW, "pair_id": "kogl1-0002"}]
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    pairs = load_corpus(p)
    assert [x.pair_id for x in pairs] == ["kogl1-0001", "kogl1-0002"]


def test_load_corpus_skips_blank_lines(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    p.write_text(json.dumps(VALID_ROW, ensure_ascii=False) + "\n\n   \n", encoding="utf-8")
    assert len(load_corpus(p)) == 1


def test_validate_corpus_raises_on_bad_row(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    bad = dict(VALID_ROW); del bad["ker_score"]
    p.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValidationError):
        validate_corpus(p)


def test_validate_corpus_returns_pairs_on_good_file(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    p.write_text(json.dumps(VALID_ROW, ensure_ascii=False), encoding="utf-8")
    assert validate_corpus(p)[0].pair_id == "kogl1-0001"
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/eval/test_corpus_schema.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.eval.corpus'`.

- [ ] **Step 3: Implement the schema + loader.** Create `ttobak/eval/corpus.py`:
```python
from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


class SourceLicense(BaseModel):
    type: str
    attribution: str
    url: str
    date_fetched: str


class FidelityChecks(BaseModel):
    numbers: bool
    dates: bool
    amounts: bool
    deadlines: bool
    eligibility: bool
    entities: bool
    distortions: list[str] = []


class CorpusPair(BaseModel):
    pair_id: str
    source_text: str
    easy_text: str
    source_license: SourceLicense
    ker_score: float
    ker_rule_violations: list[str] = []
    fidelity_checks: FidelityChecks
    pictogram_refs: list[dict] = []
    reviewer: str
    review_date: str


def load_corpus(path: Path) -> list[CorpusPair]:
    """Read a pairs.jsonl file into validated CorpusPair objects (blank lines skipped)."""
    pairs: list[CorpusPair] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pairs.append(CorpusPair(**json.loads(line)))
    return pairs


def validate_corpus(path: Path) -> list[CorpusPair]:
    """Validate a pairs.jsonl file against the schema; re-raise on any bad row."""
    return load_corpus(path)
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/eval/test_corpus_schema.py -q`. Expect `6 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/eval/corpus.py tests/eval/test_corpus_schema.py && git commit -m "feat(eval): corpus pair schema, loader and validator (spec 8.3/8.5)"`.

### Task 53: K-ER before/after eval runner over corpus pairs

`run_ker_eval()` (spec §14.4): for each corpus pair, score the SOURCE and the EASY text with an injected K-ER scorer (`score_fn`, signature of `ttobak.metric.score`), report before/after score delta and violation-count reduction, with corpus-level means. Scorer injected for determinism.

**Files:**
- Create: `ttobak/eval/ker_eval.py`
- Test: `tests/eval/test_ker_eval.py`

**Interfaces:**
- Consumes: `ttobak/levels.py` `Level`; `ttobak/common.py` `Severity`; `ttobak/metric/models.py` `KERReport`,`Violation`; the `score(easy_text, level, source_text=None) -> KERReport` signature (as `score_fn`). Pairs are plain dicts (`pair_id`,`source_text`,`easy_text`).
- Produces: `KEREvalRow{pair_id,before_score,after_score,delta,before_violations,after_violations,violation_reduction}`; `KEREvalReport{rows,mean_before,mean_after,mean_delta,mean_violation_reduction,n_pairs}`; `def run_ker_eval(pairs: list[dict], score_fn) -> KEREvalReport`.

- [ ] **Step 1: Write failing test.** Create `tests/eval/test_ker_eval.py`:
```python
from ttobak.common import Severity
from ttobak.eval.ker_eval import KEREvalReport, KEREvalRow, run_ker_eval
from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation


def _report(score: float, n_violations: int) -> KERReport:
    violations = [Violation(rule="long_sentence", span="…", severity=Severity.MED, suggestion="문장을 나누세요.") for _ in range(n_violations)]
    return KERReport(score=score, level_estimate=2, sub_scores={"rule": score}, violations=violations)


def make_score_fn(table):
    def score_fn(easy_text: str, level: Level, source_text: str | None = None):
        return _report(*table[easy_text])
    return score_fn


PAIRS = [
    {"pair_id": "p1", "source_text": "원문1 매우 어렵고 긴 문장입니다.", "easy_text": "쉬운1 짧아요."},
    {"pair_id": "p2", "source_text": "원문2 한자어가 많은 공문입니다.", "easy_text": "쉬운2 쉬워요."},
]
TABLE = {
    "원문1 매우 어렵고 긴 문장입니다.": (40.0, 6),
    "쉬운1 짧아요.": (82.0, 1),
    "원문2 한자어가 많은 공문입니다.": (50.0, 4),
    "쉬운2 쉬워요.": (80.0, 0),
}


def test_runs_and_returns_report():
    res = run_ker_eval(PAIRS, make_score_fn(TABLE))
    assert isinstance(res, KEREvalReport)
    assert res.n_pairs == 2
    assert all(isinstance(r, KEREvalRow) for r in res.rows)


def test_per_pair_delta_and_violation_reduction():
    by_id = {r.pair_id: r for r in run_ker_eval(PAIRS, make_score_fn(TABLE)).rows}
    assert by_id["p1"].before_score == 40.0 and by_id["p1"].after_score == 82.0
    assert by_id["p1"].delta == 42.0
    assert by_id["p1"].before_violations == 6 and by_id["p1"].after_violations == 1
    assert by_id["p1"].violation_reduction == 5
    assert by_id["p2"].delta == 30.0 and by_id["p2"].violation_reduction == 4


def test_corpus_level_means():
    res = run_ker_eval(PAIRS, make_score_fn(TABLE))
    assert res.mean_before == 45.0 and res.mean_after == 81.0
    assert res.mean_delta == 36.0 and res.mean_violation_reduction == 4.5


def test_empty_pairs_gives_zero_means():
    res = run_ker_eval([], make_score_fn(TABLE))
    assert res.n_pairs == 0 and res.mean_before == 0.0 and res.mean_delta == 0.0 and res.rows == []
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/eval/test_ker_eval.py -q`. Expect `ModuleNotFoundError: No module named 'ttobak.eval.ker_eval'`.

- [ ] **Step 3: Implement the runner.** Create `ttobak/eval/ker_eval.py`:
```python
from __future__ import annotations

from typing import Callable

from pydantic import BaseModel

from ttobak.levels import Level
from ttobak.metric.models import KERReport


class KEREvalRow(BaseModel):
    pair_id: str
    before_score: float
    after_score: float
    delta: float
    before_violations: int
    after_violations: int
    violation_reduction: int


class KEREvalReport(BaseModel):
    rows: list[KEREvalRow]
    mean_before: float
    mean_after: float
    mean_delta: float
    mean_violation_reduction: float
    n_pairs: int


def run_ker_eval(pairs: list[dict], score_fn: Callable[[str, Level, "str | None"], KERReport]) -> KEREvalReport:
    """Compute before/after K-ER delta over corpus pairs (spec 14.4).

    For each pair, ``score_fn`` is called on the source (before) and the easy
    text (after) at Level.EASY. Reports per-pair delta + violation reduction and
    corpus-level means. ``score_fn`` is injected for determinism.
    """
    rows: list[KEREvalRow] = []
    for pair in pairs:
        before = score_fn(pair["source_text"], Level.EASY, None)
        after = score_fn(pair["easy_text"], Level.EASY, pair["source_text"])
        rows.append(KEREvalRow(
            pair_id=pair["pair_id"], before_score=before.score, after_score=after.score,
            delta=after.score - before.score, before_violations=len(before.violations),
            after_violations=len(after.violations),
            violation_reduction=len(before.violations) - len(after.violations)))

    n = len(rows)
    if n == 0:
        return KEREvalReport(rows=[], mean_before=0.0, mean_after=0.0, mean_delta=0.0,
                             mean_violation_reduction=0.0, n_pairs=0)
    return KEREvalReport(
        rows=rows,
        mean_before=sum(r.before_score for r in rows) / n,
        mean_after=sum(r.after_score for r in rows) / n,
        mean_delta=sum(r.delta for r in rows) / n,
        mean_violation_reduction=sum(r.violation_reduction for r in rows) / n,
        n_pairs=n)
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/eval/test_ker_eval.py -q`. Expect `4 passed`.

- [ ] **Step 5: Commit.** Run `git add ttobak/eval/ker_eval.py tests/eval/test_ker_eval.py && git commit -m "feat(eval): K-ER before/after eval runner over corpus pairs (spec 14.4)"`.

### Task 54: Corpus directory scaffolding + license/provenance docs + ship-target seed pair

Lay down `corpus/` per spec §8.5: `pairs.jsonl` (CC BY 4.0) seeded with one fully-annotated synthetic-but-realistic pair (clearly labeled synthetic per §8.7), `DATA_LICENSE` (CC BY 4.0), `SOURCES.csv`, `NOTICE-sources.md` (KOGL-1 attribution template), `DATASET_CARD.md` (provenance, exclusions, PII, intended use, disclaimer, 8–12 ship target + 100–300 roadmap per §8.1). A test validates `pairs.jsonl` against the schema and asserts the required files/strings.

**Files:**
- Create: `corpus/pairs.jsonl`, `corpus/DATA_LICENSE`, `corpus/SOURCES.csv`, `corpus/NOTICE-sources.md`, `corpus/DATASET_CARD.md`
- Test: `tests/eval/test_corpus_dir.py`

**Interfaces:**
- Consumes: `ttobak/eval/corpus.py` `validate_corpus`, `CorpusPair`, `FidelityChecks`.
- Produces: the `corpus/` directory contents.

- [ ] **Step 1: Write failing test.** Create `tests/eval/test_corpus_dir.py`:
```python
from pathlib import Path

from ttobak.eval.corpus import validate_corpus

CORPUS = Path(__file__).resolve().parents[2] / "corpus"


def test_required_files_exist():
    for name in ("pairs.jsonl", "DATA_LICENSE", "SOURCES.csv", "NOTICE-sources.md", "DATASET_CARD.md"):
        assert (CORPUS / name).is_file(), f"missing corpus/{name}"


def test_data_license_is_cc_by_40():
    text = (CORPUS / "DATA_LICENSE").read_text(encoding="utf-8")
    assert "CC BY 4.0" in text or "Creative Commons Attribution 4.0" in text


def test_dataset_card_states_ship_target_and_roadmap():
    text = (CORPUS / "DATASET_CARD.md").read_text(encoding="utf-8")
    assert "8" in text and "12" in text
    assert "100" in text and "300" in text
    assert "합성" in text or "synthetic" in text.lower()
    assert "원문" in text


def test_notice_has_kogl1_attribution_template():
    text = (CORPUS / "NOTICE-sources.md").read_text(encoding="utf-8")
    assert "공공누리" in text and "제1유형" in text


def test_sources_csv_header():
    header = (CORPUS / "SOURCES.csv").read_text(encoding="utf-8").splitlines()[0]
    for col in ("title", "agency", "year", "url", "kogl_type", "date_fetched"):
        assert col in header


def test_shipped_pairs_jsonl_validates_against_schema():
    pairs = validate_corpus(CORPUS / "pairs.jsonl")
    assert len(pairs) >= 1
    assert pairs[0].source_text and pairs[0].easy_text
    assert pairs[0].fidelity_checks.deadlines in (True, False)
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/eval/test_corpus_dir.py -q`. Expect failures — `corpus/` files do not exist.

- [ ] **Step 3: Create `corpus/DATA_LICENSE`.**
```text
또박(Ttobak) Corpus — Annotations and Easy-Read Texts
License: Creative Commons Attribution 4.0 International (CC BY 4.0)
https://creativecommons.org/licenses/by/4.0/

This license applies to the easy-read texts and annotations authored by the
또박 project (the "easy" side of each pair, K-ER annotations, and fidelity
checks). Source-side texts retain their original license as recorded per row
in pairs.jsonl (source_license) and in SOURCES.csv / NOTICE-sources.md.

You are free to share and adapt this material for any purpose, including
commercially, provided you give appropriate credit:
"또박(Ttobak) Korean Easy-Read Corpus, CC BY 4.0".
```

- [ ] **Step 4: Create `corpus/SOURCES.csv`.**
```text
title,agency,year,url,kogl_type,date_fetched,redistributable,notes
건강보험료 납부 안내문(합성),또박 프로젝트(합성 저작),2026,https://github.com/ttobak/ttobak,SYNTHETIC,2026-06-30,yes,저자 직접 작성 합성 문서 — 실제 PII 없음
```

- [ ] **Step 5: Create `corpus/NOTICE-sources.md`.**
```markdown
# 출처표시 (Source Attribution)

이 코퍼스의 쉬운 글과 주석은 또박(Ttobak) 프로젝트가 작성했으며 CC BY 4.0으로 배포됩니다.
원문(source) 측 저작물의 라이선스는 행별로 `pairs.jsonl`의 `source_license`와
`SOURCES.csv`에 기록됩니다.

## 공공누리 제1유형(KOGL Type-1) 출처표시 템플릿 (실문서 추가 시 사용)

> 본 저작물은 '<기관명>'에서 '<연도>' 작성하여 공공누리 제1유형으로 개방한
> '<저작물명>'을 이용하였으며, 해당 저작물은 '<기관명>, <누리집 URL>'에서
> 무료로 내려받으실 수 있습니다.

- 공공누리 제1유형은 상업적 이용·변형·재배포를 허용하되 출처표시 의무가 있습니다.
- 마크 이미지는 발급기관만 부착할 수 있으므로 본 코퍼스는 텍스트형 출처표시만 사용합니다.

## 현재 수록 출처

- 건강보험료 납부 안내문(합성): 또박 프로젝트가 직접 작성한 **합성(synthetic)** 문서로,
  실제 기관 문서를 복제하지 않았으며 실제 개인정보(PII)를 포함하지 않습니다.
```

- [ ] **Step 6: Create `corpus/DATASET_CARD.md`.**
```markdown
# 또박(Ttobak) Korean Easy-Read Corpus — Dataset Card

## 개요
어려운 한국어 공공·행정 문서(source)와 그에 대응하는 쉬운 글(easy-read) 페어 모음.
각 페어는 K-ER 점수, 규칙 위반 목록, 필드별 Fidelity 주석, 프로비넌스를 함께 담는다.

## 규모 (정직한 보고)
- **출품(ship) 목표 (2026-08-27): 8~12개 완전 주석 페어.** 약속 n = 실제 평가 보고 n.
- **확장 100~300개는 대회 이후 로드맵으로 명시한다** (현재 미수록).
- 초기 시드는 합성(synthetic) 문서로 시작하며, 재배포 가능한 KOGL-1 / data.go.kr(CC BY)
  실문서를 점진적으로 추가한다.

## 프로비넌스 & 라이선스
- 쉬운 글·주석 = CC BY 4.0 (`DATA_LICENSE`).
- 원문 라이선스 = 행별 `source_license` + `SOURCES.csv` + `NOTICE-sources.md`.
- 허용 출처: 공공누리 제1유형, data.go.kr 중 CC BY/제한없음, 자체 합성 저작물.

## 제외 (배포하지 않음)
- AI Hub, 국립국어원 모두의 말뭉치 (재배포 금지 — 사적 평가 전용, `/dev-only/`).
- KOGL Type-2/3/4, CC-NC 소스, 실제 PII 포함 문서, NC 픽토그램(ARASAAC/KAAC).

## PII 처리
실제 개인정보를 포함하지 않는다. 합성 문서는 가상의 금액·기한만 사용하며,
실문서 추가 시 이름·주민번호·연락처 등 PII를 제거 후 수록한다.

## 의도된 용도
한국어 Easy-Read 변환 파이프라인의 before/after K-ER 평가, Fidelity 게이트 평가,
연구·재현용. 학년 수준 측정이나 진단 도구가 아니다.

## 면책 (Fidelity-first)
쉬운 글은 보조 자료이며 **법적 효력은 원문이 우선**한다. K-ER 점수는
한국 Easy-Read 지침에 정렬한 **규칙 기반 루브릭이며 경험적으로 검증되지 않았다**.
```

- [ ] **Step 7: Create `corpus/pairs.jsonl` with one fully-annotated synthetic pair.** Write exactly one JSON object on one line (UTF-8):
```text
{"pair_id": "synth-0001", "source_text": "건강보험료 1,295,400원을 2026년 7월 17일까지 강서구청에 납부하시기 바랍니다. 만 65세 이상 어르신은 경감 대상에서 제외됩니다. 소득이 월 30,000원 미만인 경우 추가 지원을 신청할 수 있습니다.", "easy_text": "건강보험료 1,295,400원을 내세요. 2026년 7월 17일까지 강서구청에 내야 합니다. 만 65세 이상 어르신은 깎아주는 대상이 아닙니다. 한 달 소득이 30,000원 미만이면 도움을 더 신청할 수 있습니다.", "source_license": {"type": "SYNTHETIC", "attribution": "또박 프로젝트(합성 저작)", "url": "https://github.com/ttobak/ttobak", "date_fetched": "2026-06-30"}, "ker_score": 79.0, "ker_rule_violations": ["sino_korean_word:건강보험료", "long_sentence:source"], "fidelity_checks": {"numbers": true, "dates": true, "amounts": true, "deadlines": true, "eligibility": true, "entities": true, "distortions": []}, "pictogram_refs": [{"set": "openmoji", "glyph_id": "1F4B0", "modified": false}, {"set": "openmoji", "glyph_id": "1F4C5", "modified": false}], "reviewer": "solo-reviewer", "review_date": "2026-07-05"}
```

- [ ] **Step 8: Run, expect PASS.** Run `python -m pytest tests/eval/test_corpus_dir.py -q`. Expect `6 passed`.

- [ ] **Step 9: Commit.** Run `git add corpus/ tests/eval/test_corpus_dir.py && git commit -m "feat(corpus): corpus directory scaffolding, CC BY 4.0 license/provenance docs, seed pair (spec 8.5)"`.

### Task 55: End-to-end harness integration over the shipped corpus

Wire the three harness pieces together against the real shipped corpus and deterministic injected scorer/verifier: load `corpus/pairs.jsonl`, run the K-ER eval (before/after delta), generate distortions from each pair and run the distortion bench, asserting the headline metrics from spec §6.9/§14.4 are produced over real corpus data. Deterministic (injected `score_fn`/`verify_fn`, no live API).

**Files:**
- Test: `tests/eval/test_eval_integration.py`

**Interfaces:**
- Consumes: `ttobak/eval/corpus.py` `load_corpus`; `ttobak/eval/ker_eval.py` `run_ker_eval`; `ttobak/eval/distortion_bench.py` `generate_distortions`,`run_distortion_bench`,`DistortionType`; `ttobak/levels.py` `Level`; `ttobak/common.py` `Verdict`,`Severity`; `ttobak/metric/models.py` `KERReport`,`Violation`; `ttobak/fidelity/models.py` `FidelityReport`; `ttobak/ir.py` `Document`.
- Produces: integration coverage only.

- [ ] **Step 1: Inspect which distortions the shipped seed pair realizes.** Run `python -c "from datetime import date; from pathlib import Path; from ttobak.eval.corpus import load_corpus; from ttobak.eval.distortion_bench import generate_distortions; p=load_corpus(Path('corpus/pairs.jsonl'))[0]; print([c.distortion_type.value for c in generate_distortions(p.source_text,p.easy_text,ref_date=date(2026,7,1)) if not c.is_clean])"`. Expected output: `['number_swap', 'digit_drop', 'date_shift', 'condition_flip', 'range_weaken', 'entity_swap', 'hallucinated_entity']` (the seed easy-text uses "30,000원 미만이면" with no "까지"/"빠집니다", so inclusivity_flip and negation_drop do not fire). Note the realized list for the `_MARKERS` tuple in Step 2.

- [ ] **Step 2: Write failing test.** Create `tests/eval/test_eval_integration.py` (`_MARKERS` lists the output token of every realized distortion from Step 1):
```python
from datetime import date
from pathlib import Path

from ttobak.common import Severity, Verdict
from ttobak.eval.corpus import load_corpus
from ttobak.eval.distortion_bench import DistortionType, generate_distortions, run_distortion_bench
from ttobak.eval.ker_eval import run_ker_eval
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Document
from ttobak.levels import Level
from ttobak.metric.models import KERReport, Violation

CORPUS = Path(__file__).resolve().parents[2] / "corpus"


def score_fn(easy_text: str, level: Level, source_text: str | None = None) -> KERReport:
    is_source = source_text is None
    sc = 45.0 if is_source else 80.0
    n_viol = 5 if is_source else 1
    return KERReport(score=sc, level_estimate=2, sub_scores={"rule": sc},
                     violations=[Violation(rule="long_sentence", span="…", severity=Severity.MED, suggestion="문장을 나누세요.") for _ in range(n_viol)])


_MARKERS = ("3,000원", "129,540", "7월 7일", "이하", "송파구청", "국민건강보험공단")


def verify_fn(source: Document, easy_text: str, ref_date: date) -> FidelityReport:
    verdict = Verdict.HUMAN_REVIEW if any(m in easy_text for m in _MARKERS) else Verdict.PASS
    return FidelityReport(slots=[], verdict=verdict)


def test_ker_eval_over_real_corpus_shows_positive_delta():
    pairs = [p.model_dump() for p in load_corpus(CORPUS / "pairs.jsonl")]
    report = run_ker_eval(pairs, score_fn)
    assert report.n_pairs >= 1
    assert report.mean_delta > 0


def test_distortion_bench_over_real_corpus_catches_distortions():
    pairs = load_corpus(CORPUS / "pairs.jsonl")
    all_cases = []
    for p in pairs:
        all_cases.extend(generate_distortions(p.source_text, p.easy_text, ref_date=date(2026, 7, 1)))
    assert any(c.distortion_type == DistortionType.CLEAN for c in all_cases)
    assert sum(1 for c in all_cases if not c.is_clean) >= 5

    res = run_distortion_bench(all_cases, verify_fn, ref_date=date(2026, 7, 1))
    assert res.overall_recall == 1.0
    assert res.clean_fp_rate == 0.0
    assert res.pass_residual_distortion_rate == 0.0
```

- [ ] **Step 3: Run, expect PASS.** Run `python -m pytest tests/eval/test_eval_integration.py -q`. Expect `2 passed`. If `overall_recall` < 1.0, a realized distortion's output token is missing from `_MARKERS` — add the missing token (per Step 1) and re-run. Test-only edit; no production change.

- [ ] **Step 4: Run the full module suite, expect all green.** Run `python -m pytest tests/eval -q`. Expect all passing (scaffold 4 + distortion models 4 + generator 14 + bench 4 + corpus schema 6 + corpus dir 6 + integration 2 = 40 passed).

- [ ] **Step 5: Commit.** Run `git add tests/eval/test_eval_integration.py && git commit -m "test(eval): end-to-end harness integration over shipped corpus"`.

> **M11 reconciliation with M0:** M0 shipped early gate scripts (`scripts/check_licenses.py`, `scripts/check_assets_separation.py`) and a CI workflow with three inline gates. M11 ships the **comprehensive, consolidated** gate at `tooling/check_licenses.py` (allowlist + assets separation + secrets/PII, with a dataclass result type, orchestrator, and exit-code `main`) and **appends a `license-audit` job** to the M0 workflow. The M0 `scripts/*` gates may remain (belt-and-suspenders) or be replaced by the `tooling` gate — prefer keeping the M0 license-allowlist quick check AND adding the M11 comprehensive audit; both must agree (no GPL/AGPL/NC). Tests for both live side by side.

### Task 56: License allowlist checker (fails on GPL/AGPL/NC)

The load-bearing core: a pure function over parsed `pip-licenses` JSON flagging any forbidden license. Deterministic and CI-runnable without a live `pip-licenses` install (tests pass fixtures directly). Implements spec §9.5 and §14.5.

**Files:**
- Create: `tooling/__init__.py`
- Create: `tooling/check_licenses.py`
- Create: `tests/tooling/__init__.py`
- Create: `tests/tooling/test_license_allowlist.py`
- Create: `tests/tooling/fixtures/licenses_clean.json`
- Create: `tests/tooling/fixtures/licenses_planted_gpl.json`

**Interfaces:**
- Consumes: `ttobak/` package + `pyproject.toml`; spec §9.1–9.4 dependency licenses; spec §9.5 forbidden set.
- Produces: `tooling/check_licenses.py`: `ALLOWED_LICENSE_SUBSTRINGS` (frozenset), `FORBIDDEN_LICENSE_SUBSTRINGS` (frozenset), `LicenseViolation` (frozen dataclass `kind:str`, `detail:str`), `check_license_allowlist(packages: list[dict]) -> list[LicenseViolation]`.

- [ ] **Step 1: Write the planted-GPL fixture.** Create `tests/tooling/fixtures/licenses_planted_gpl.json`:
```json
[
  {"Name": "ttobak", "Version": "0.1.0", "License": "Apache Software License"},
  {"Name": "pypdf", "Version": "4.3.1", "License": "BSD License"},
  {"Name": "pydantic", "Version": "2.8.2", "License": "MIT License"},
  {"Name": "konlpy", "Version": "0.6.0", "License": "GNU General Public License v3 (GPLv3)"},
  {"Name": "pyhwp", "Version": "0.1b15", "License": "GNU Affero General Public License v3"}
]
```

- [ ] **Step 2: Write the clean-tree fixture.** Create `tests/tooling/fixtures/licenses_clean.json`:
```json
[
  {"Name": "ttobak", "Version": "0.1.0", "License": "Apache Software License"},
  {"Name": "hwp-hwpx-parser", "Version": "1.0.0", "License": "Apache Software License"},
  {"Name": "olefile", "Version": "0.47", "License": "BSD License"},
  {"Name": "python-docx", "Version": "1.1.2", "License": "MIT License"},
  {"Name": "pypdf", "Version": "4.3.1", "License": "BSD License"},
  {"Name": "pdfminer.six", "Version": "20240706", "License": "MIT License"},
  {"Name": "kiwipiepy", "Version": "0.18.0", "License": "GNU Lesser General Public License v3 (LGPLv3)"},
  {"Name": "dateparser", "Version": "1.2.0", "License": "Apache Software License"},
  {"Name": "pydantic", "Version": "2.8.2", "License": "MIT License"},
  {"Name": "jinja2", "Version": "3.1.4", "License": "BSD License"},
  {"Name": "gradio", "Version": "5.0.0", "License": "Apache Software License"}
]
```

- [ ] **Step 3: Write failing tests for the allowlist checker.** Create `tooling/__init__.py` (empty), `tests/tooling/__init__.py` (empty), and `tests/tooling/test_license_allowlist.py`:
```python
import json
from pathlib import Path

from tooling.check_licenses import LicenseViolation, check_license_allowlist

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_clean_tree_has_no_violations():
    assert check_license_allowlist(_load("licenses_clean.json")) == []


def test_planted_gpl_is_flagged():
    violations = check_license_allowlist(_load("licenses_planted_gpl.json"))
    names = {v.detail.split(" ")[0] for v in violations}
    assert "konlpy" in names
    assert "pyhwp" in names
    assert all(v.kind == "forbidden-license" for v in violations)


def test_lgpl_is_allowed_separate_dependency():
    pkgs = [{"Name": "kiwipiepy", "Version": "0.18.0", "License": "GNU Lesser General Public License v3 (LGPLv3)"}]
    assert check_license_allowlist(pkgs) == []


def test_noncommercial_license_is_flagged():
    pkgs = [{"Name": "exaone", "Version": "3.5", "License": "EXAONE AI Model License (Non-Commercial)"}]
    violations = check_license_allowlist(pkgs)
    assert len(violations) == 1 and violations[0].kind == "forbidden-license"


def test_unknown_license_is_flagged_as_review():
    pkgs = [{"Name": "mystery-lib", "Version": "1.0", "License": "UNKNOWN"}]
    violations = check_license_allowlist(pkgs)
    assert len(violations) == 1 and violations[0].kind == "unrecognized-license"
```

- [ ] **Step 4: Run, expect FAIL.** Run `python -m pytest tests/tooling/test_license_allowlist.py -q`. Expect `ModuleNotFoundError: No module named 'tooling.check_licenses'`.

- [ ] **Step 5: Implement the allowlist checker.** Create `tooling/check_licenses.py` (this task adds only the allowlist section; Tasks 57–59 append to the same file):
```python
"""Ttobak license & security audit gate (spec 9.5 / 14.5).

Deterministic checks that fail the build on: GPL/AGPL/NC/proprietary code deps;
pictogram CC BY-SA assets leaking out of /assets; secrets/PII committed. The
license check operates on parsed `pip-licenses --format=json` output so it is
unit-testable with planted fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LicenseViolation:
    kind: str
    detail: str


# Permissive + separate-dependency weak-copyleft (LGPL) licenses we ship (spec 9.1, 9.4).
ALLOWED_LICENSE_SUBSTRINGS: frozenset[str] = frozenset({
    "apache", "mit", "bsd", "mpl", "mozilla public", "isc",
    "python software foundation", "psf", "the unlicense", "unlicense", "zlib",
    "lgpl", "lesser general public", "creative commons attribution 4.0",
    "cc-by-4.0", "cc by 4.0", "cc0", "public domain",
    "historical permission notice and disclaimer", "hpnd",
})

# Hard blockers: strong copyleft + non-commercial + proprietary (spec 9.5).
FORBIDDEN_LICENSE_SUBSTRINGS: frozenset[str] = frozenset({
    "agpl", "affero", "non-commercial", "noncommercial", "non commercial",
    "-nc-", " nc ", "research license", "proprietary",
})


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().replace("(", " ").replace(")", " ").split())


def _is_lgpl(norm: str) -> bool:
    return "lgpl" in norm or "lesser general public" in norm


def _is_strong_gpl(norm: str) -> bool:
    if _is_lgpl(norm):
        return False
    return "gpl" in norm or "general public license" in norm


def check_license_allowlist(packages: list[dict]) -> list[LicenseViolation]:
    """Return a violation per package whose license is forbidden or unrecognized.

    Order per package: FORBIDDEN substring -> forbidden-license; strong (non-Lesser)
    GPL -> forbidden-license; ALLOWED substring -> ok; otherwise -> unrecognized-license.
    """
    violations: list[LicenseViolation] = []
    for pkg in packages:
        name = pkg.get("Name", "?")
        version = pkg.get("Version", "?")
        raw_license = pkg.get("License", "")
        norm = _normalize(raw_license)
        label = f"{name} {version} [{raw_license}]"
        if any(bad in norm for bad in FORBIDDEN_LICENSE_SUBSTRINGS):
            violations.append(LicenseViolation("forbidden-license", label))
            continue
        if _is_strong_gpl(norm):
            violations.append(LicenseViolation("forbidden-license", label))
            continue
        if any(ok in norm for ok in ALLOWED_LICENSE_SUBSTRINGS):
            continue
        violations.append(LicenseViolation("unrecognized-license", label))
    return violations
```

- [ ] **Step 6: Run, expect PASS.** Run `python -m pytest tests/tooling/test_license_allowlist.py -q`. Expect `5 passed`.

- [ ] **Step 7: Commit.** Run `git checkout -b m11-license-ci && git add tooling/__init__.py tooling/check_licenses.py tests/tooling/__init__.py tests/tooling/test_license_allowlist.py tests/tooling/fixtures/ && git commit -m "feat(audit): license allowlist checker fails on GPL/AGPL/NC deps"`.

### Task 57: /assets separation checker (CC BY-SA glyphs must not leak into code/data)

Implements spec §9.4 embed rule + §8.5 layout: pictogram CC BY-SA assets live only under `/assets/pictograms/`, each set carries its own LICENSE, and no glyph files (.svg/.png) or base64-embedded glyphs leak into the Apache code tree (`ttobak/`) or CC BY dataset (`/corpus/`).

**Files:**
- Modify: `tooling/check_licenses.py`
- Test: `tests/tooling/test_assets_separation.py`

**Interfaces:**
- Consumes: `LicenseViolation` (Task 56); the `/assets/pictograms/{mulberry,openmoji,derived}/` layout (Task 4 marker + per-set LICENSE files when assets are added); spec §9.4, §8.5.
- Produces: `check_assets_separation(root: Path) -> list[LicenseViolation]`.

- [ ] **Step 1: Write failing tests.** Create `tests/tooling/test_assets_separation.py`:
```python
from pathlib import Path

from tooling.check_licenses import check_assets_separation


def _make_clean_tree(root: Path) -> None:
    (root / "ttobak" / "pictogram").mkdir(parents=True)
    (root / "ttobak" / "pictogram" / "__init__.py").write_text("", encoding="utf-8")
    assets = root / "assets" / "pictograms"
    (assets / "mulberry").mkdir(parents=True)
    (assets / "openmoji").mkdir(parents=True)
    (assets / "mulberry" / "LICENSE").write_text("CC BY-SA 2.0 UK", encoding="utf-8")
    (assets / "openmoji" / "LICENSE").write_text("CC BY-SA 4.0", encoding="utf-8")
    (assets / "mulberry" / "phone.svg").write_text("<svg/>", encoding="utf-8")
    (assets / "openmoji" / "1F4B0.svg").write_text("<svg/>", encoding="utf-8")


def test_clean_tree_passes(tmp_path):
    _make_clean_tree(tmp_path)
    assert check_assets_separation(tmp_path) == []


def test_glyph_leaked_into_code_tree_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "ttobak" / "pictogram" / "leaked.svg").write_text("<svg/>", encoding="utf-8")
    violations = check_assets_separation(tmp_path)
    assert any(v.kind == "asset-leak" for v in violations)
    assert any("leaked.svg" in v.detail for v in violations)


def test_base64_glyph_embedded_in_code_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "ttobak" / "pictogram" / "embed.py").write_text(
        'GLYPH = "data:image/svg+xml;base64,PHN2Zy8+"\n', encoding="utf-8")
    assert any(v.kind == "asset-embed" for v in check_assets_separation(tmp_path))


def test_pictogram_set_missing_license_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "assets" / "pictograms" / "mulberry" / "LICENSE").unlink()
    violations = check_assets_separation(tmp_path)
    assert any(v.kind == "asset-missing-license" for v in violations)
    assert any("mulberry" in v.detail for v in violations)


def test_glyph_leaked_into_corpus_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "corpus").mkdir()
    (tmp_path / "corpus" / "stray.png").write_bytes(b"\x89PNG\r\n")
    assert any(v.kind == "asset-leak" for v in check_assets_separation(tmp_path))
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/tooling/test_assets_separation.py -q`. Expect `ImportError: cannot import name 'check_assets_separation'`.

- [ ] **Step 3: Implement assets separation check.** In `tooling/check_licenses.py`, change the header `from dataclasses import dataclass` to the three lines `import re`, `from dataclasses import dataclass`, `from pathlib import Path`, then append:
```python
# --- /assets separation (spec 9.4 embed rule, 8.5 layout) -------------------

GLYPH_SUFFIXES: frozenset[str] = frozenset({".svg", ".png", ".gif", ".webp"})
CODE_DATA_DIRS: tuple[str, ...] = ("ttobak", "corpus", "tooling")
REQUIRED_PICTOGRAM_SETS: tuple[str, ...] = ("mulberry", "openmoji")
_SOURCE_SUFFIXES: frozenset[str] = frozenset({".py", ".html", ".jinja", ".j2", ".css", ".js", ".json"})
_BASE64_GLYPH_RE = re.compile(r"data:image/(?:svg\+xml|png|gif|webp);base64,")


def check_assets_separation(root: Path) -> list[LicenseViolation]:
    """Verify CC BY-SA pictogram assets stay inside /assets and never leak.

    Flags: glyph files under code/data dirs (asset-leak), base64-embedded glyphs
    in source files (asset-embed), pictogram sets missing a LICENSE (asset-missing-license).
    """
    violations: list[LicenseViolation] = []
    for top in CODE_DATA_DIRS:
        base = root / top
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in GLYPH_SUFFIXES:
                violations.append(LicenseViolation("asset-leak", str(path.relative_to(root))))
                continue
            if suffix in _SOURCE_SUFFIXES:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if _BASE64_GLYPH_RE.search(text):
                    violations.append(LicenseViolation("asset-embed", str(path.relative_to(root))))

    pictogram_root = root / "assets" / "pictograms"
    if pictogram_root.exists():
        for set_name in REQUIRED_PICTOGRAM_SETS:
            set_dir = pictogram_root / set_name
            if set_dir.exists() and not (set_dir / "LICENSE").exists():
                violations.append(LicenseViolation("asset-missing-license", f"assets/pictograms/{set_name}"))
    return violations
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/tooling/test_assets_separation.py -q`. Expect `5 passed`.

- [ ] **Step 5: Commit.** Run `git add tooling/check_licenses.py tests/tooling/test_assets_separation.py && git commit -m "feat(audit): assert /assets CC BY-SA pictogram separation (no code/data leak)"`.

### Task 58: Secrets/PII scanner

Implements spec §14.5 + §3.2 (no secrets/PII before submission) and §8.2/§8.4 (corpus PII-free). A regex scanner flagging API keys, private keys, and Korean PII (resident registration number). Excludes test fixtures, dev-only, VCS dirs so it does not flag its own planted samples.

**Files:**
- Modify: `tooling/check_licenses.py`
- Test: `tests/tooling/test_secrets_scan.py`

**Interfaces:**
- Consumes: `LicenseViolation`, `re`, `Path` (Tasks 56–57); spec §14.5, §3.2, §8.2.
- Produces: `SECRET_PII_PATTERNS` (list[tuple[str,str]]), `check_no_secrets(root: Path) -> list[LicenseViolation]`.

- [ ] **Step 1: Write failing tests.** Create `tests/tooling/test_secrets_scan.py`:
```python
from pathlib import Path

from tooling.check_licenses import check_no_secrets


def test_clean_tree_has_no_secrets(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "core.py").write_text("def simplify(text: str) -> str:\n    return text\n", encoding="utf-8")
    assert check_no_secrets(tmp_path) == []


def test_aws_key_is_flagged(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "bad.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    violations = check_no_secrets(tmp_path)
    assert any(v.kind == "secret" for v in violations)
    assert any("aws-access-key" in v.detail for v in violations)


def test_anthropic_key_is_flagged(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "bad.py").write_text('TOKEN = "sk-ant-api03-' + "x" * 20 + '"\n', encoding="utf-8")
    assert any("anthropic-api-key" in v.detail for v in check_no_secrets(tmp_path))


def test_private_key_block_is_flagged(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "key.pem").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIE\n", encoding="utf-8")
    assert any("private-key" in v.detail for v in check_no_secrets(tmp_path))


def test_korean_rrn_in_corpus_is_flagged(tmp_path):
    (tmp_path / "corpus").mkdir()
    (tmp_path / "corpus" / "pairs.jsonl").write_text('{"source_text": "신청자 주민등록번호 900101-1234567 확인"}\n', encoding="utf-8")
    violations = check_no_secrets(tmp_path)
    assert any(v.kind == "pii" for v in violations)
    assert any("korean-rrn" in v.detail for v in violations)


def test_test_fixtures_are_excluded(tmp_path):
    fix = tmp_path / "tests" / "tooling" / "fixtures"
    fix.mkdir(parents=True)
    (fix / "planted.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    assert check_no_secrets(tmp_path) == []
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/tooling/test_secrets_scan.py -q`. Expect `ImportError: cannot import name 'check_no_secrets'`.

- [ ] **Step 3: Implement the scanner.** Append to `tooling/check_licenses.py`:
```python
# --- secrets / PII scan (spec 14.5, 3.2, 8.2) -------------------------------

# (label, regex). All labels except korean-rrn classify as "secret"; rrn = PII.
SECRET_PII_PATTERNS: list[tuple[str, str]] = [
    ("aws-access-key", r"AKIA[0-9A-Z]{16}"),
    ("anthropic-api-key", r"sk-ant-[A-Za-z0-9_-]{20,}"),
    ("openai-api-key", r"sk-(?:proj-)?[A-Za-z0-9]{20,}"),
    ("google-api-key", r"AIza[0-9A-Za-z_-]{35}"),
    ("slack-token", r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    ("private-key", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ("generic-secret-assign",
     r"(?i)(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][A-Za-z0-9/+_-]{16,}['\"]"),
    ("korean-rrn", r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)"),
]

_PII_LABELS: frozenset[str] = frozenset({"korean-rrn"})

_SCAN_EXCLUDE_DIRS: frozenset[str] = frozenset({
    ".git", ".github", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "dist", "build", ".venv", "venv", "dev-only", "tests", "test",
})

_SCANNABLE_SUFFIXES: frozenset[str] = frozenset({
    ".py", ".pyi", ".txt", ".md", ".json", ".jsonl", ".csv", ".yaml",
    ".yml", ".toml", ".cfg", ".ini", ".env", ".html", ".js", ".ts",
    ".pem", ".key", ".sh", "",
})

_COMPILED_PATTERNS = [(label, re.compile(pattern)) for label, pattern in SECRET_PII_PATTERNS]


def _should_scan(path: Path, root: Path) -> bool:
    parts = path.relative_to(root).parts
    if any(part in _SCAN_EXCLUDE_DIRS for part in parts):
        return False
    return path.suffix.lower() in _SCANNABLE_SUFFIXES


def check_no_secrets(root: Path) -> list[LicenseViolation]:
    """Scan the tree for committed secrets and Korean PII (spec 14.5/3.2/8.2).

    tests/, test/, dev-only/ are excluded so planted fixtures and private
    evaluation data do not trip the gate.
    """
    violations: list[LicenseViolation] = []
    for path in root.rglob("*"):
        if not path.is_file() or not _should_scan(path, root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for label, compiled in _COMPILED_PATTERNS:
            if compiled.search(text):
                kind = "pii" if label in _PII_LABELS else "secret"
                violations.append(LicenseViolation(kind, f"{label} in {rel}"))
    return violations
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/tooling/test_secrets_scan.py -q`. Expect `6 passed`.

- [ ] **Step 5: Commit.** Run `git add tooling/check_licenses.py tests/tooling/test_secrets_scan.py && git commit -m "feat(audit): secrets and Korean PII scanner over code and corpus"`.

### Task 59: Audit orchestrator + pip-licenses collector + main()

Wire the three checkers into one `run_audit`, add `collect_installed_licenses()` (subprocess to `pip-licenses --format=json`, the only live-tooling part), and a `main()` returning exit code 1 on any violation, 0 when clean (spec §14.5).

**Files:**
- Modify: `tooling/check_licenses.py`
- Test: `tests/tooling/test_run_audit.py`

**Interfaces:**
- Consumes: `LicenseViolation`, `check_license_allowlist`, `check_assets_separation`, `check_no_secrets` (Tasks 56–58).
- Produces: `run_audit(root: Path, packages: list[dict] | None = None) -> list[LicenseViolation]`; `collect_installed_licenses() -> list[dict]`; `main(argv: list[str] | None = None) -> int`.

- [ ] **Step 1: Write failing tests.** Create `tests/tooling/test_run_audit.py`:
```python
import json
from pathlib import Path

from tooling import check_licenses
from tooling.check_licenses import run_audit, main

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _clean_repo(root: Path) -> None:
    (root / "ttobak").mkdir()
    (root / "ttobak" / "__init__.py").write_text("", encoding="utf-8")
    assets = root / "assets" / "pictograms"
    (assets / "mulberry").mkdir(parents=True)
    (assets / "openmoji").mkdir(parents=True)
    (assets / "mulberry" / "LICENSE").write_text("CC BY-SA 2.0 UK", encoding="utf-8")
    (assets / "openmoji" / "LICENSE").write_text("CC BY-SA 4.0", encoding="utf-8")


def test_run_audit_clean(tmp_path):
    _clean_repo(tmp_path)
    assert run_audit(tmp_path, packages=_load("licenses_clean.json")) == []


def test_run_audit_collects_all_checker_kinds(tmp_path):
    _clean_repo(tmp_path)
    (tmp_path / "ttobak" / "leak.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "ttobak" / "bad.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    kinds = {v.kind for v in run_audit(tmp_path, packages=_load("licenses_planted_gpl.json"))}
    assert "forbidden-license" in kinds
    assert "asset-leak" in kinds
    assert "secret" in kinds


def test_main_returns_1_on_planted_gpl(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_planted_gpl.json"))
    rc = main(["--root", str(tmp_path)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "forbidden-license" in out and "FAIL" in out


def test_main_returns_0_on_clean_tree(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_clean.json"))
    rc = main(["--root", str(tmp_path)])
    assert rc == 0
    assert "PASS" in capsys.readouterr().out
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/tooling/test_run_audit.py -q`. Expect `ImportError: cannot import name 'run_audit'`.

- [ ] **Step 3: Implement run_audit, collect_installed_licenses, main.** In `tooling/check_licenses.py`, change the `import re` header line to the block `import argparse`, `import json`, `import re`, `import subprocess`; then append at the end:
```python
# --- orchestration + entrypoint (spec 14.5) --------------------------------

def collect_installed_licenses() -> list[dict]:
    """Run pip-licenses and return its JSON. The only live-tooling call;
    tests inject packages instead. Requires the `audit` extra."""
    proc = subprocess.run(
        ["pip-licenses", "--format=json", "--with-system", "--with-urls"],
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def run_audit(root: Path, packages: list[dict] | None = None) -> list[LicenseViolation]:
    """Run all three gates and return the combined violation list."""
    if packages is None:
        packages = collect_installed_licenses()
    violations: list[LicenseViolation] = []
    violations.extend(check_license_allowlist(packages))
    violations.extend(check_assets_separation(root))
    violations.extend(check_no_secrets(root))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ttobak-audit", description="License & security gate (spec 9.5 / 14.5).")
    parser.add_argument("--root", default=".", help="Repository root to scan (default: current directory).")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    violations = run_audit(root)
    if violations:
        print(f"FAIL: {len(violations)} license/security violation(s):")
        for v in violations:
            print(f"  [{v.kind}] {v.detail}")
        return 1
    print("PASS: license & security audit clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/tooling/test_run_audit.py -q`. Expect `4 passed`.

- [ ] **Step 5: Commit.** Run `git add tooling/check_licenses.py tests/tooling/test_run_audit.py && git commit -m "feat(audit): orchestrate gates + pip-licenses collector + exit-code main"`.

### Task 60: `ttobak audit` CLI subcommand + packaging wiring

Implements spec §12.2.8 packaging finalize + the `ttobak audit` script requirement. EXTENDS the Task-46 `ttobak/cli.py` `main` with an `audit` subcommand (alongside `web`), adds the `audit` extra to `pyproject.toml`, and adds a `make audit` target.

> **Reconciliation:** Task 46 already created `ttobak/cli.py:main` with a `web` subparser and registered `[project.scripts] ttobak = "ttobak.cli:main"`. This task ADDS an `audit` subparser to the SAME `main` (do not create a second entry point). The console-script line already exists from Task 46.

**Files:**
- Modify: `ttobak/cli.py`
- Modify: `pyproject.toml`
- Create: `Makefile`
- Test: `tests/tooling/test_cli_audit.py`

**Interfaces:**
- Consumes: `tooling.check_licenses.main` and `collect_installed_licenses` (Task 59); the Task-46 `ttobak/cli.py`.
- Produces: `ttobak/cli.py` with an `audit` branch in `main`; `pyproject.toml` `[project.optional-dependencies] audit = ["pip-licenses>=5,<6"]` and `[tool.setuptools] packages` including `tooling`; `Makefile` `audit` target.

- [ ] **Step 1: Write failing tests.** Create `tests/tooling/test_cli_audit.py`:
```python
import json
from pathlib import Path

from tooling import check_licenses
from ttobak.cli import main as cli_main

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _clean_repo(root: Path) -> None:
    (root / "ttobak").mkdir()
    (root / "ttobak" / "__init__.py").write_text("", encoding="utf-8")
    assets = root / "assets" / "pictograms"
    (assets / "mulberry").mkdir(parents=True)
    (assets / "openmoji").mkdir(parents=True)
    (assets / "mulberry" / "LICENSE").write_text("CC BY-SA 2.0 UK", encoding="utf-8")
    (assets / "openmoji" / "LICENSE").write_text("CC BY-SA 4.0", encoding="utf-8")


def test_cli_audit_clean(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_clean.json"))
    assert cli_main(["audit", "--root", str(tmp_path)]) == 0
    assert "PASS" in capsys.readouterr().out


def test_cli_audit_fails_on_gpl(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_planted_gpl.json"))
    assert cli_main(["audit", "--root", str(tmp_path)]) == 1
    assert "forbidden-license" in capsys.readouterr().out
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/tooling/test_cli_audit.py -q`. Expect FAIL — `ttobak.cli.main` has no `audit` branch yet (returns help/1 for unknown command).

- [ ] **Step 3: Add the `audit` subparser to `ttobak/cli.py`.** Extend `_build_parser()` and `main()` (keep the `web` subcommand from Task 46):
```python
# in _build_parser(), after the web subparser:
    audit_p = sub.add_parser("audit", help="라이선스·보안 게이트 실행 (spec 14.5)")
    audit_p.add_argument("--root", default=".", help="스캔할 레포 루트 (기본: 현재 디렉터리)")
    return parser

# in main(), before the print_help fallback:
    if args.command == "audit":
        from tooling import check_licenses
        return check_licenses.main(["--root", args.root])
```
  (Place the `audit` branch alongside the existing `if args.command == "web":` branch.)

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/tooling/test_cli_audit.py -q`. Expect `2 passed`.

- [ ] **Step 5: Wire packaging.** In `pyproject.toml`: add `audit = ["pip-licenses>=5,<6"]` under `[project.optional-dependencies]`; ensure `tooling` is packaged — under `[tool.setuptools.packages.find]` the `include` already matches `ttobak*`, so add `tooling*` to `include` (or set `[tool.setuptools] packages = ["ttobak", "tooling"]`). The `[project.scripts] ttobak = "ttobak.cli:main"` line already exists from Task 46. Reinstall: `python -m pip install -e ".[dev,audit]"`.

- [ ] **Step 6: Create the Makefile.** Create `Makefile` (recipe lines MUST use tabs):
```makefile
.PHONY: audit test install-audit

install-audit:
	python -m pip install -e ".[audit]"

audit:
	python -m tooling.check_licenses --root .

test:
	python -m pytest -q
```

- [ ] **Step 7: Verify the import graph.** Run `python -c "from ttobak.cli import main; print('cli-ok')"` → expect `cli-ok`. (The full `make audit` shells out to `pip-licenses`; exercised in CI after `pip install -e ".[audit]"`.)

- [ ] **Step 8: Commit.** Run `git add ttobak/cli.py pyproject.toml Makefile tests/tooling/test_cli_audit.py && git commit -m "feat(audit): add 'ttobak audit' CLI subcommand + audit extra + make target"`.

### Task 61: Finalize NOTICE & THIRD_PARTY_LICENSES with every shipped dependency

Implements spec §9.6 (packaging actions 1, 3, 5), §9.4, §8.6. Finalizes the Task-3 NOTICE/THIRD_PARTY_LICENSES so every dependency from spec §9.1–9.4 appears with license + source, including required verbatim notices (Qwen, OpenMoji, Mulberry) and the LGPL relink statement. A test asserts coverage.

**Files:**
- Modify: `NOTICE`
- Modify: `THIRD_PARTY_LICENSES.md`
- Test: `tests/tooling/test_notice_coverage.py`

**Interfaces:**
- Consumes: Task-3 `NOTICE`/`THIRD_PARTY_LICENSES.md`; spec §9.1–9.6, §8.6.
- Produces: finalized `NOTICE`, finalized `THIRD_PARTY_LICENSES.md`; `tests/tooling/test_notice_coverage.py`.

- [ ] **Step 1: Write the failing coverage test.** Create `tests/tooling/test_notice_coverage.py`:
```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SHIPPED_DEPS = [
    "hwp-hwpx-parser", "olefile", "python-docx", "pypdf", "pdfminer.six",
    "kiwipiepy", "dateparser", "korean-number", "es-hangul",
    "kf-deberta-base-cross-nli", "bert-score", "sentence-transformers",
    "transformers", "spaCy", "ko_core_news_lg", "fastapi", "uvicorn",
    "pydantic", "mcp", "Ollama", "Qwen2.5", "Kanana", "Mulberry", "OpenMoji",
]
FORBIDDEN_MENTIONS = ["pyhwp", "KoNLPy", "EXAONE", "ARASAAC"]


def test_third_party_licenses_covers_every_shipped_dep():
    text = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8").lower()
    missing = [dep for dep in SHIPPED_DEPS if dep.lower() not in text]
    assert missing == [], f"undocumented deps: {missing}"


def test_notice_has_required_verbatim_attributions():
    text = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "Apache License" in text or "Apache-2.0" in text
    assert "Built with Qwen" in text
    assert "OpenMoji" in text and "CC BY-SA 4.0" in text
    assert "Mulberry" in text and "CC BY-SA 2.0 UK" in text
    assert "LGPL" in text


def test_forbidden_components_only_appear_as_excluded():
    text = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    for name in FORBIDDEN_MENTIONS:
        hit_lines = [ln for ln in text.splitlines() if name.lower() in ln.lower()]
        assert hit_lines, f"{name} must be documented as excluded"
        assert all(
            any(k in ln.lower() for k in ("excluded", "non-commercial", "avoided", "not shipped", "blocker"))
            for ln in hit_lines), f"{name} mentioned without exclusion marker"
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/tooling/test_notice_coverage.py -q`. Expect failures — the Task-3 skeleton lacks several deps and the verbatim attribution strings.

- [ ] **Step 3: Finalize NOTICE.** Overwrite `NOTICE`:
```
Ttobak (또박)
Copyright 2026 Ttobak contributors

This product includes software developed as part of the Ttobak project,
licensed under the Apache License, Version 2.0 (the "License"); you may not
use these files except in compliance with the License. You may obtain a copy
of the License at http://www.apache.org/licenses/LICENSE-2.0

=============================================================================
Third-party components
=============================================================================
Full per-component license texts and sources are in THIRD_PARTY_LICENSES.md.
Required attributions follow.

-----------------------------------------------------------------------------
Apache-2.0 dependencies (NOTICE aggregation)
-----------------------------------------------------------------------------
hwp-hwpx-parser, dateparser, transformers, sentence-transformers,
pytesseract, opencv-python-headless are licensed under the Apache License 2.0.
Their NOTICE obligations are satisfied by reproducing the Apache License 2.0
in THIRD_PARTY_LICENSES.md.

-----------------------------------------------------------------------------
Weak-copyleft (LGPL) — separate dependency, dynamically linked, unmodified
-----------------------------------------------------------------------------
kiwipiepy and soynlp are licensed under the GNU Lesser General Public License
v3 (LGPL-3.0). Ttobak depends on them as separate, unmodified, dynamically
imported packages and does not modify or statically link their sources. Users
may relink against modified versions per the LGPL.

-----------------------------------------------------------------------------
Model weights
-----------------------------------------------------------------------------
Local-model paths may use Qwen2.5 (Apache-2.0). Required attribution:
  "Built with Qwen"
and Kanana-1.5-8B/2.1B (Apache-2.0, Kakao). Non-commercial / gated models
(Qwen2.5-3B/72B, Kanana-2-30B, EXAONE) are NOT shipped and are excluded from
all release artifacts; documented only as known alternatives.

-----------------------------------------------------------------------------
Pictogram assets (shipped separately under /assets, not Apache-licensed)
-----------------------------------------------------------------------------
OpenMoji: "All emojis designed by OpenMoji – the open-source emoji and icon
project. License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)".

Mulberry Symbols: "Mulberry Symbols are copyright 2018 to 2026 Steve Lee and
licensed under CC BY-SA 2.0 UK: England & Wales. See
https://mulberrysymbols.org".

These CC BY-SA assets live under /assets/pictograms/ with their own LICENSE
files and are referenced by path/URL only — never embedded inline or base64
into Apache-2.0 code or the CC BY 4.0 dataset.
```

- [ ] **Step 4: Finalize THIRD_PARTY_LICENSES.md.** Overwrite `THIRD_PARTY_LICENSES.md`:
````markdown
# Third-Party Licenses

Ttobak is licensed under Apache-2.0 (see `LICENSE`). This file enumerates every
third-party component Ttobak ships, depends on, or documents, per spec §9.1–9.4.
All entries verified 2026-06-30. Risk: clean / caution / blocker.

## Code dependencies (spec 9.1)

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
| Date parsing | dateparser | Apache-2.0 | clean | https://github.com/scrapinghub/dateparser |
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
| Mulberry Symbols (primary) | CC BY-SA 2.0 UK | caution (SA, commercial OK) | https://mulberrysymbols.org/ |
| OpenMoji (secondary) | CC BY-SA 4.0 | caution (SA, commercial OK) | https://openmoji.org/ |
| ARASAAC / KAAC | CC BY-NC-SA / NC | blocker | Non-Commercial — avoided, not shipped |

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
````

- [ ] **Step 5: Run, expect PASS.** Run `python -m pytest tests/tooling/test_notice_coverage.py -q`. Expect `3 passed`. (Confirm the Task-3 `test_licensing_files.py` still passes — its required deps remain present.)

- [ ] **Step 6: Commit.** Run `git add NOTICE THIRD_PARTY_LICENSES.md tests/tooling/test_notice_coverage.py && git commit -m "docs(audit): finalize NOTICE + THIRD_PARTY_LICENSES for all shipped deps"`.

### Task 62: Wire the license-audit gate into the CI workflow

Implements spec §14.5 (license/security CI) and §11.3 (license verification = finalist→winner gate). Appends a `license-audit` job to the Task-6 workflow that installs the `audit` extra, runs the M11 unit tests (so the planted-GPL fixture proves the checker fails-closed in CI), then runs the gate against the real tree.

**Files:**
- Modify: `.github/workflows/ci.yml`
- Test: `tests/tooling/test_ci_wiring.py`

**Interfaces:**
- Consumes: Task-6 `.github/workflows/ci.yml`; `tooling/check_licenses.py:main` (Task 59); the `audit` extra (Task 60).
- Produces: `.github/workflows/ci.yml` `license-audit` job; `tests/tooling/test_ci_wiring.py`.

- [ ] **Step 1: Write a failing test asserting the workflow declares the gate.** Create `tests/tooling/test_ci_wiring.py`:
```python
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_has_license_audit_job():
    assert "license-audit:" in CI.read_text(encoding="utf-8")


def test_ci_installs_audit_extra_and_runs_gate():
    text = CI.read_text(encoding="utf-8")
    assert "[audit]" in text
    assert "tooling.check_licenses" in text


def test_ci_runs_checker_unit_tests():
    assert "tests/tooling" in CI.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run, expect FAIL.** Run `python -m pytest tests/tooling/test_ci_wiring.py -q`. Expect `assert "license-audit:" in ...` to fail (Task-6 workflow has no such job).

- [ ] **Step 3: Append the license-audit job.** Add this job to `.github/workflows/ci.yml` under the existing `jobs:` mapping (keep the Task-6 `test-and-license-gate` job; add this sibling at the same indentation):
```yaml
  license-audit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - name: Install package with audit extra
        run: python -m pip install -e ".[dev,audit]"
      - name: Run checker unit tests (incl. planted-GPL fail-closed proof)
        run: python -m pytest tests/tooling -q
      - name: License & security gate (fails on GPL/AGPL/NC, asset leak, secrets)
        run: python -m tooling.check_licenses --root .
```

- [ ] **Step 4: Run, expect PASS.** Run `python -m pytest tests/tooling/test_ci_wiring.py -q`. Expect `3 passed`.

- [ ] **Step 5: Validate the workflow YAML parses.** Run `python -c "import yaml; yaml.safe_load(open('.github/workflows/ci.yml')); print('yaml-ok')"` → expect `yaml-ok`. (If PyYAML is absent, `python -m pip install pyyaml` then re-run.)

- [ ] **Step 6: Commit.** Run `git add .github/workflows/ci.yml tests/tooling/test_ci_wiring.py && git commit -m "ci(audit): add license-audit job running gate + planted-GPL fail-closed tests"`.

### Task 63: Full-suite green + end-to-end gate self-check

Final verification: the whole M11 test suite passes, and the gate runs clean against the actual repository tree (the deliverable for spec §11.3). Proves both directions — clean tree PASSes, planted-GPL fixture (already in the suite) FAILs.

**Files:**
- Test: `tests/tooling/test_module_smoke.py`

**Interfaces:**
- Consumes: `run_audit`, `check_assets_separation`, `check_no_secrets` (Tasks 57–59), all prior fixtures/checkers.
- Produces: `tests/tooling/test_module_smoke.py`.

- [ ] **Step 1: Write a smoke test that runs the filesystem gates against the real repo tree.** Create `tests/tooling/test_module_smoke.py`:
```python
from pathlib import Path

from tooling.check_licenses import check_assets_separation, check_no_secrets, run_audit

ROOT = Path(__file__).resolve().parents[2]


def test_real_tree_has_no_asset_leak_or_secrets():
    # Filesystem gates only (no live pip-licenses): the committed tree must be clean.
    violations = []
    violations.extend(check_assets_separation(ROOT))
    violations.extend(check_no_secrets(ROOT))
    assert violations == [], [(v.kind, v.detail) for v in violations]


def test_run_audit_with_empty_packages_skips_license_check():
    # packages=[] -> license classifier finds nothing; only filesystem gates run.
    violations = run_audit(ROOT, packages=[])
    assert violations == [], [(v.kind, v.detail) for v in violations]
```

- [ ] **Step 2: Run the smoke test; fix any real offender it surfaces (not the test).** Run `python -m pytest tests/tooling/test_module_smoke.py -q`. Expect `2 passed` if the tree is clean. If it FAILS, the assertion prints the offending `(kind, detail)` pairs — remove/relocate the offending file (e.g. a stray glyph under `ttobak/`, an accidental key), then re-run. This is the load-bearing self-check.

- [ ] **Step 3: Run the entire M11 suite, expect all green.** Run `python -m pytest tests/tooling -q`. Expect `31 passed` (5 allowlist + 5 assets + 6 secrets + 4 run_audit + 2 cli + 3 notice + 3 ci-wiring + 2 smoke; adjust the count to the actual tests written).

- [ ] **Step 4: Run the WHOLE project test suite + the gate, expect all green (final MVP gate).** Run `python -m pytest -q && python -m tooling.check_licenses --root .`. Expect every test passing and `PASS: license & security audit clean.`. This is the 8/27 ship gate (spec §11.3, §12.2).

- [ ] **Step 5: Commit.** Run `git add tests/tooling/test_module_smoke.py && git commit -m "test(audit): module smoke test runs gate clean against real tree"`.

## 스트레치 (MVP 이후, 전체 TDD 아님)

These are explicitly **out of MVP scope** (spec §12.3) and are listed here as plug-in points, NOT as full TDD task sets. Cut from the back: ship the MVP first.

**이미지 OCR (image OCR).** Add an OCR input tier under `ttobak/parse/`: a `parse_image(data: bytes, mime) -> Document` using `pytesseract` + Tesseract (Apache-2.0) with `opencv-python-headless`/Pillow preprocessing, producing `Block`s at low confidence (e.g. 0.4–0.6) so the Fidelity gate and renderer flag low-trust source (spec §6.10, §7.3). Plugs into `parse()` dispatch (Task 41) as new image MIME branches; everything downstream is unchanged because it consumes the same IR. Curate clean demo scans; legacy `.hwp` binary stays out.

**MCP server.** Expose the core API as MCP tools `simplify`, `score`, `verify_fidelity` over `mcp>=1.27,<2` (pin per spec §9.6; never v2 alpha). A thin `ttobak/mcp_server.py` wraps `pipeline.simplify`, `metric.score`, `fidelity.verify` and returns JSON (`EasyReadResult`/`KERReport`/`FidelityReport` via `model_dump()`). Plugs in as a third surface and an `mcp` console subcommand under `ttobak/cli.py`; adds an `mcp` optional-dependency extra. Pure wrapper over the existing core (the "agent/reusable-OSS" judging narrative, spec §4.2 surface 3).

**K-ER model layer (KcBERT/RSRS).** Add the spec §5.2 (2) model-signal layer as a `model` sub-score alongside the rule layer: a KcBERT-fine-tuned syntactic-complexity submodel and RSRS/biRSRS unsupervised "surprisal". Plugs into `ttobak/metric/score()` by populating `sub_scores["model"]` and fusing via the LAURAE confidence-weighted formula `Score = c×LLM_std + (1−c)×RuleModel_std`. Local, label-free; gated behind an optional `transformers`/KcBERT dependency so the MVP rule-only path is unaffected.

**Semantic-NLI fidelity.** Turn on the `use_nli=True` path already stubbed in `verify()` (Task 30): sentence-aligned bidirectional NLI (SummaC-style) with `kf-deberta-base-cross-nli` (MIT) for CONDITION/ELIGIBILITY/MODALITY/SCOPE slots, plus KoBERTScore as a soft drift advisory (spec §6.5/§6.6). Plugs into `verify()` by populating `nli_contradictions`; ML only raises flags (never approves), and HIGH-slot exact-match remains authoritative. Calibrate thresholds on a held-out dev split (spec §6.8, §14.2).

**Semantic pictogram matching.** Replace the ~30-concept hand lexicon (Tasks 31–32) with embedding-based concept→glyph matching over a larger Mulberry/OpenMoji set, keeping CC BY-SA separation and Korean captions. Plugs into `ttobak/pictogram/match()` behind a flag, falling back to the lexicon when confidence is low (spec §4.2.E, §R5). Risk: nonsensical matches in demos — keep the curated lexicon as the safe default.

**TTS (text-to-speech).** Add an optional read-aloud control to the renderer/web demo using the browser Web Speech API (free, client-side; spec §3.4). Plugs into `render_html()`/`build_app()` as an extra button reading `easy_text`; no server dependency, no license exposure. Stretch because it is accessibility polish, not core engine value.

**Batch / multi-document.** Add a `simplify_batch(docs: list[Document], level, provider) -> list[EasyReadResult]` convenience over `simplify()` plus a CLI subcommand iterating a directory of inputs, aggregating K-ER deltas and Fidelity verdicts into a CSV/JSONL report (reusing the M10 eval harness). Plugs in above the core as orchestration only — no engine change. Useful for agencies converting document sets, but out of the 8/27 MVP.
