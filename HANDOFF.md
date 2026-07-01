# HANDOFF — 2026 오픈소스 개발자대회 출품작 "또박(Ttobak)"

## 현재 상태 — ✅ MVP 코드 완성 · main 머지 완료
**또박(Ttobak) MVP 63 TDD 태스크 전부 구현 + 최종 리뷰 5건 수정 완료, `main`에 머지(75 커밋), 331 테스트 통과, `ttobak audit` 클린.** SDD(subagent-driven) + 다중 에이전트 배치 워크플로우 + 적대적 최종 리뷰로 구현.
- 동작 확인(런타임): `parse(텍스트/PDF/HWPX)→simplify(생성→측정→교정 루프)→render_html` end-to-end. **Fidelity 게이트 적대적 검증 통과** — 금액 반올림(약 130만 원)·날짜 까지↔전에·자격 이상↔이하/미만↔이하 플립을 잡아 REVISE/HUMAN_REVIEW, 충실 문장은 PASS. K-ER 규칙점수 + 위반 체크리스트 동작.
- 코드: `ttobak/`(40 모듈) + `tests/`(65+ 파일). 웹 데모 `ttobak web`(Gradio), 평가 `ttobak.eval`(distortion bench + K-ER eval + corpus), 라이선스/보안 `ttobak audit`(GPL/AGPL/NC 차단, 프로젝트 closure 스코핑).
- 문서: 스펙 `docs/superpowers/specs/2026-06-30-ttobak-easy-read-engine-design.md`, 계획 `docs/superpowers/plans/2026-06-30-ttobak-mvp.md`, SDD 원장 `.superpowers/sdd/progress.md`(완료 태스크·커밋 SHA·이슈 — 신뢰원천).

## 다음 스텝 — 대회 출품 준비 (코드 외, 오늘 7/1 기준)
✅ **개발계획서(7/17) 초안 완성** → `docs/contest/2026-개발계획서-또박.md` (12절, ~16KB). 실코드 기반 병렬추출→종합→정직성 적대검증→수정 워크플로우로 작성. 적대검증이 실결함 2건 교정: (a) §7.3 머니샷 수치(revisions=1/K-ER 79.3/exact_fail=2)는 '약 130만 원+7월' 결합 시나리오 관측값이지 반올림 단독 경로 수치 아님 → 정확 귀속. (b) OpenMoji는 코퍼스 seed glyph 참조로만 존재하고 렉시콘(match 코드)엔 미배선 → Mulberry만 배선됨으로 정정. **주의: §2 통계 2건(쉬운정보 공급 1% 미만 / 성인 문해력 20.1%)은 에이전트 웹리서치 출처라 최종 제출 전 1차 출처 재확인 필요.** 남은 건 공식 oss.kr 양식(hwp)에 붙여넣기.
✅ **공개 코퍼스 11쌍 완성** → `corpus/pairs.jsonl` (synth-0001~0011, 전부 합성, **사람 최종 검수 예정**). 실측 K-ER: 원문 72.0 → 쉬운 글 81.8 (**Δ+9.8**, n=11), 위반 −2.45, 전 페어 Fidelity PASS. 문서유형별 저자→주석기 오라클로 PASS까지 반복→**적대적 충실성 감사** 워크플로우로 제작. **핵심 산물: 11쌍 전부 자동 게이트는 통과했으나 감사가 7쌍에서 게이트 사각(가능→명령 modality, 소득인정액→소득, AND조건 분해, 검진기관→병원 범위축소, 무주택 세대구성원→개인)을 잡음 → 글로싱으로 재작성 후 재감사 통과. = 보고서/영상의 강력한 "정직성" 서사.** 재현용 주석기 `tooling/annotate_corpus.py` 신규 추가(실엔진 실행으로 주석 도출). 프로비넌스 파일(SOURCES.csv·NOTICE-sources.md·DATASET_CARD.md) 11쌍 반영. 개발계획서 §4.2/§7/§9.4/일정/각주도 n=11로 정합화.
  - 부수 발견: 기존 seed(구 synth-0001)는 '제외됩니다'→'아닙니다'로 바꿔 실제로는 human_review였고 등재 79.0도 실측 79.9와 불일치 → 재생성으로 해소. **게이트 authoring 규칙: 원문 부정 키워드(제외/불가/없)를 쉬운본에 어미까지 verbatim 유지해야 PASS**(동의어 치환 시 NegationGuard가 human_review). 테스트 `test_eval_integration.py`의 스텁-마커 배선 테스트가 다양한 코퍼스에서 오탐 → **실제 게이트를 shipped 코퍼스에 돌리는 정직한 테스트로 교체**(clean_fp==0 + 담당유형 recall==1.0, entity_swap/hallucinated는 out-of-scope 명시). 전체 331 통과 유지.
- 남은 출품물: ① **개발(결과)보고서**(8/27) — 계획서와 60~70% 겹침, 계획서+코퍼스 실측 재활용. ② **3분 데모 영상** — 머니샷 3경로(반올림 REVISE→교정, 이상↔이하 HUMAN_REVIEW, 날짜) + 코퍼스 before/after. ③ **GitHub 공개 레포 푸시**(현재 로컬, 원격 미설정) — 8/27용, 7/17 블로커 아님(공고 확인). ④ 코퍼스 **사람 최종 검수** + 재배포 가능 KOGL-1 실문서 2~3건 보강(선택).
- 이번 세션 신규 확인 결함(정직성 검증 산물): **NOTICE가 미사용 soynlp를 LGPL 의존성으로 과다 기재**(pyproject·THIRD_PARTY·import 어디에도 없음, 코드 주석에만) → 10월 라이선스 검증 전 정리(별도 태스크 flag됨). 라이선스 게이트가 `scripts/`와 `tooling/check_licenses.py` 두 곳 부분 중복 → 통합 여지.
- 알려진 Minor(원장 참조): easy_words.txt(211개) 확장으로 R-02 false-positive 감소, gradio gr.HTML padding=True, 추출기 확장(NUMERIC 원없는수·AGENCY·PERSON·hallucinated-entity는 MVP 미적용).

## 확정된 프로젝트
**또박(Ttobak)** — 어려운 한국어 공공·생활 문서(공문·고지서)를 "쉬운 정보(Easy-Read)"로 바꾸고 *쉬움을 측정해 스스로 교정*하는 오픈소스(Apache-2.0) 엔진. 트랙=자유과제(AI), 일반부문 솔로. 대상: 1차 발달장애인·경계선지능, 2차 노인·이주민·저문해 + 생산측 공무원. 차별점: 온글(폐쇄 SaaS)·WIA(감각 접근성) 대비 *열린·측정가능·자가교정·포맷네이티브* 인지 접근성 엔진. "한국어 Easy-Read 최초"는 주장 안 함(정직성=해자).

## 라이선스(클린 — 대회 검증 관문 통과 확인)
코드 Apache-2.0 / 데이터 CC BY / 자산 분리 CC BY-SA. HWP=hwp-hwpx-parser(Apache, pyhwp/AGPL 회피); 형태소=kiwipiepy(LGPL, KoNLPy/GPL 회피); 픽토그램=Mulberry+OpenMoji(CC BY-SA, ARASAAC/KAAC NC 회피); 로컬LLM=Qwen2.5/Kanana-1.5(Apache, EXAONE/Kanana-2 NC 제외). ⚠️ 공유 dev 환경엔 무관 AGPL/GPL(PyMuPDF/pyphen) 존재 — 게이트는 프로젝트 closure 기준이라 통과.

## 대회 일정 (검증: 과기정통부 2026-06-15 보도/NIPA 공고)
개발계획서 **7/17** · 출품 **8/27**(보고서+3분영상+소스) · 1차서면 ~9/3(결선 50) · 멘토링 9/18~10/9 · 라이선스·기능 검증 10/12~28 · 2차발표 11/4 · 시상 12/5. 일반부 대상 1,000만원.

## 피해야 할 레드오션 (라이브 검증 — 강한/다수 인큐번트, 또박 후보 선정 시 회피)
보이스피싱(SilverGuard), 법률셀프구제(korean-certified-mail/caseLaw), 이주민행정(UMMAYA/ASKOVISA), 한국수어, 산업안전(Safety Lens), 웹접근성수정(OpenSpec), 농작물병해충, 한국점자(braillify), 제주어, 차트음향화(chart2music/maidr). 인접: WIA 글살림·GongMun-Doctor·kordoc(파서는 재사용).
