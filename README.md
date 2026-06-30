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
