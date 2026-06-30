# HANDOFF — 2026 오픈소스 개발자대회 출품작 "또박(Ttobak)" 설계

## 현재 작업
**구현 진행 중** — Task4 리뷰 픽스 완료 (8dcdbd6).
- 스펙: `docs/superpowers/specs/2026-06-30-ttobak-easy-read-engine-design.md` (15절, critic 14건 반영).
- 계획: `docs/superpowers/plans/2026-06-30-ttobak-mvp.md` (**63 TDD 태스크, 3 Phase**; M0~M11). Phase1 Tasks 1~20=코어 골격(텍스트 입력 end-to-end).
- 브랜치 `impl/ttobak-mvp`. Task4 assets-guard 리뷰 픽스 커밋 완료 (#1 전체 파일 스캔, #3 대소문자 무감, #4 상대 경로 skip). 테스트 19/19 통과.
- 각 Task 리포트: `.superpowers/sdd/task-N-report.md`

## 다음 스텝
Task5+ (리더 파이프라인) 계속 실행. subagent-driven-development 또는 executing-plans로 진행.

## 확정된 프로젝트
**또박(Ttobak)** — 어려운 한국어 공공·생활 문서(공문·고지서)를 "쉬운 정보(Easy-Read)"로 바꾸고 *쉬움을 측정해 스스로 교정*하는 오픈소스 엔진. 트랙=자유과제(AI), 일반부문 솔로.
- 대상: 1차 발달장애인·경계선지능, 2차 노인·이주민·저학력 + 생산측 공무원.
- 아키텍처: 파싱(HWP/HWPX/PDF/이미지OCR/텍스트)→Easy-Read 생성→측정(K-ER 지표)→교정 루프 + **Fidelity 게이트(의미 보존, 1급 안전)** → 픽토그램 → 렌더. 표면 3개: Python 패키지 + 웹 데모 + MCP 서버.
- 4대 OSS 자산: ① 생성→측정→교정 에이전트 루프 ② 한국어 이지리드 가독성 지표(K-ER, 공개 부재 → 직접 공개) ③ 공개 평가 코퍼스 ④ 픽토그램 매칭.

## 라이선스(클린 확정 — 대회 라이선스 검증 관문 대비)
- HWP/HWPX = `hwp-hwpx-parser`(PyPI, **Apache-2.0**). pyhwp(AGPL) 회피.
- 픽토그램 = Mulberry + OpenMoji(**CC BY-SA**, 자산 분리·출처표시). ARASAAC(BY-NC-SA)·한국 KAAC(비상업) 회피.
- 로컬 LLM = Qwen2.5(Ollama, **Apache-2.0**). EXAONE/Kanana=NC는 옵션·문서화.
- 형태소분석기 GPL(KoNLPy+mecab) 주의 → 비-GPL 대안 선택(워크플로우가 확정).
- 프로젝트 코드 라이선스 = Apache-2.0 권장. 코퍼스 = CC BY/CC0.

## 대회 일정 (검증됨: 과기정통부 2026-06-15 보도/NIPA 공고)
참가신청·개발계획서 **7/17** · 출품 **8/27**(보고서+3분영상+소스) · 1차서면 ~9/3(결선 50) · 멘토링 9/18~10/9 · **라이선스·기능 검증 10/12~28** · 2차발표 11/4 · 시상 12/5. 일반부 대상 1,000만원.

## 피해야 할 레드오션 (이번 세션 라이브 검증 — 전부 강한/다수 인큐번트)
보이스피싱탐지(SilverGuard 등), 법률셀프구제(korean-certified-mail/caseLaw 등), 이주민행정(UMMAYA/ASKOVISA 등), 한국수어, 산업안전위험성평가(Safety Lens 등), 웹접근성자동수정(OpenSpec 등), 농작물병해충, 한국점자(braillify 174★), 제주어, 차트음향화(chart2music/maidr). 인접 주의: WIA 글살림(접근성 종합 플랫폼), GongMun-Doctor-MCP(공문교정), kordoc-ai(문서변환) — 또박은 *발달장애인 전용 + 측정가능 + Fidelity게이트*로 차별화. (이전 세션의 에이전트 인프라 레드오션 목록도 유효.)
