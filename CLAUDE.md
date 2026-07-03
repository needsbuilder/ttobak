# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트

**또박(Ttobak)** — 어려운 한국어 공공·행정 문서를 "쉬운 정보(Easy-Read)"로 변환하는 오픈소스 엔진. 쉬움을 K-ER 점수로 측정하고, Fidelity 게이트로 사실(숫자·날짜·금액·기한·자격·기관명)을 보존하며 자가 교정한다. 2026 오픈소스 개발자대회 출품작. 코드 Apache-2.0 / 데이터(corpus) CC BY 4.0 / 픽토그램(assets) CC BY-SA — 세 라이선스는 절대 섞이면 안 된다(아래 라이선스 절 참조).

상세 스펙은 `docs/superpowers/plans/2026-06-30-ttobak-mvp.md` — 코드 docstring의 "spec 6.8" 같은 인용이 가리키는 문서다.

## 명령어

```bash
python -m pip install -e ".[dev]"        # 설치 (Python 3.11+; 로컬 venv/ 존재, CI는 3.11/3.12)
python -m pytest -q                      # 전체 테스트 (= make test)
python -m pytest tests/fidelity -q       # 한 디렉터리만
python -m pytest tests/fidelity/test_verify.py -q          # 한 파일만
python -m pytest -k "negation" -q        # 이름 매칭
python -m tooling.check_licenses --root .  # 라이선스·보안 게이트 (= make audit = ttobak audit)
python scripts/check_licenses.py         # CI Gate 2: pip-licenses 허용목록 (GPL/AGPL/NC 시 실패)
ttobak web --provider fake               # Gradio 웹 데모 (fake = API 키 불필요)
python -m tooling.annotate_corpus --seed # corpus/pairs.jsonl 첫 페어만 재채점 (검증용)
python -m tooling.annotate_corpus "<원문>" "<쉬운본>"  # 단일 페어 채점 (실제 엔진 실행, JSON 출력)
```

린터/포매터 설정 없음. CI(`.github/workflows/ci.yml`)는 pytest + 라이선스 허용목록 + assets 분리 검사 + 감사 게이트 4중이다.

## 아키텍처

파이썬 코어 `ttobak/`가 6개 공개 함수를 노출하고, 웹 데모·평가 하네스는 전부 이 코어의 얇은 래퍼다:

```
parse()    ttobak/parse/     텍스트·PDF·HWPX → IR Document (mime 디스패치)
score()    ttobak/metric/    K-ER 규칙 루브릭: 12개 규칙 평균 0–100 + Violation 체크리스트
verify()   ttobak/fidelity/  슬롯 추출 → HIGH 슬롯 정확일치 검증 → NegationGuard/드리프트 → 판정
match()    ttobak/pictogram/ 픽토그램 렉시콘 룩업 (경로 참조만)
simplify() ttobak/pipeline.py GENERATE → MEASURE → REVISE 루프 오케스트레이션
render_html() ttobak/render.py 원문/쉬운본 나란히 HTML + 면책 + 배지 (Jinja2)
```

**공유 계약 (canonical — 재정의 금지, 반드시 import):**
- `ttobak/ir.py` — `Document`/`Block`/`BlockType` (모든 모듈이 쓰는 IR)
- `ttobak/common.py` — `Severity`, `Verdict(PASS/REVISE/HUMAN_REVIEW)`
- `ttobak/levels.py` — `Level(EASY/PLAIN)`
- `ttobak/result.py` — `EasyReadResult` (`simplify()`의 출력 모델)

**파이프라인 핵심 규칙 (`pipeline.py`):**
- 재교정 루프는 **Fidelity 판정이 REVISE일 때만** 돈다. K-ER 점수는 트리거가 아니다(의도된 MVP 설계).
- `HUMAN_REVIEW`(예: 부정 극성 반전, 날짜 포함관계·경계연산자 드리프트)는 즉시 종료하며 절대 자동 교정하지 않는다.
- `max_revise` 소진 후 잔존 REVISE는 HUMAN_REVIEW로 승격 (fail-safe).
- `score`/`verify`는 테스트 monkeypatch를 위해 모듈 레벨에서 import되어 있다 — 이 구조를 깨지 말 것.

**LLM 프로바이더 (`ttobak/providers/`):** `LLMProvider` Protocol + 팩토리 `get_provider()`. `fake`(테스트 전용 — 테스트는 절대 라이브 API를 치지 않는다), `anthropic`(데모 기본), `ollama`(로컬, 기본 `kanana-1.5-8b`). 실제 SDK는 생성 시점에 lazy import — optional extras 없이도 패키지가 import돼야 한다. `ttobak/web/provider.py`의 `make_provider()`는 이름 미지정 시 `$TTOBAK_PROVIDER` → `anthropic` 순으로 고르고, API 키 부재 시 FakeProvider로 폴백한다(CI 안전성).

**평가 (`ttobak/eval/`, `tooling/annotate_corpus.py`):** 코퍼스(`corpus/pairs.jsonl`) 주석은 손으로 지어내지 않는다 — 반드시 실제 엔진을 실행해 도출한다(재현 가능성 = 정직성). gold 페어는 fidelity 게이트 `verdict == PASS`여야 한다.

## 라이선스 — 하드 게이트 (CI가 빌드를 깬다)

- **금지 의존성:** GPL/AGPL/NC. 대체 확정: pyhwp(AGPL)→hwp-hwpx-parser, KoNLPy(GPL)→kiwipiepy(LGPL, 분리 의존).
- **Qwen2.5는 사이즈별 라이선스가 다르다:** 0.5B/1.5B/7B/14B/32B = Apache-2.0, **3B/72B = NC(Qwen Research License)**. 문서·데모·NOTICE에는 7B/14B만 인용. `THIRD_PARTY_LICENSES.md`가 신뢰 원천.
- **`assets/`(픽토그램, CC BY-SA)는 Apache 코드 트리와 분리 유지.** 렌더러는 픽토그램을 파일 경로/URL 참조로만 쓴다 — 수정된 글리프를 inline/base64로 코드·데이터 출력에 내장 금지(`scripts/check_assets_separation.py`가 CI에서 검사).
- 의존성 추가 시 `THIRD_PARTY_LICENSES.md`·`NOTICE` 갱신 필요 (`tests/tooling/test_notice_coverage.py`가 검증).
- `dev-only/`는 비배포 평가 자료 — 절대 커밋 금지 (.gitignore 처리됨).

## 정직성 원칙 (출력·문서 작성 시 유지)

- K-ER은 **규칙 기반 루브릭이며 경험적으로 검증된 지표가 아니다** — 이 단서를 문서·출력에서 제거하지 말 것. 점수는 보조 지표, 위반 체크리스트가 핵심 산출물.
- 모든 렌더 출력에 면책 문구가 항상 포함된다. `render.py`의 "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다"는 템플릿 테스트가 verbatim으로 assert하는 문자열이다.
- "한국어 Easy-Read AI 최초" 류의 주장 금지 (선행 존재: 온글 등).
- 쉬움과 충실성이 충돌하면 **충실성이 이긴다** (Fidelity-first).

## 컨벤션

- TDD: 실패 테스트 먼저 → red → 구현 → green → 커밋 (플랜 문서가 강제하는 루프).
- 커밋: Conventional Commits + 스코프 — `feat(corpus):`, `fix(fidelity):`, `ci(audit):`, `docs(license):`.
- docstring은 한국어·영어 혼용이며 스펙 절 번호를 인용한다 (예: "spec 6.8").
- pydantic v2 모델로 계약을 정의한다. 테스트는 도메인별 디렉터리(`tests/fidelity/`, `tests/metric/`, …)로 미러링.
