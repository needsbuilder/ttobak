# 또박(Ttobak) — 한국어 쉬운 정보(Easy-Read) 엔진 설계 명세서

> 설계 명세 작성일: 2026-06-30 · 라이선스/문헌/경쟁/코퍼스/타당성 근거는 본 세션에서 라이브 웹 검증 완료(각 절에 출처 URL·일자 명시).
> 대회: 2026 오픈소스 개발자대회(과기정통부/NIPA), 자유과제(AI), 일반부문, 1인(solo).
> **본 명세는 구현 착수 가능한 단일 문서(self-contained)다. 미확정 항목은 14·15절에 "내린 결정 + 가정"으로 명시했고, TODO/TBD 플레이스홀더는 두지 않는다.**

---

## 1. 개요

### 1.1 한 줄 정의
**또박은 어려운 한국어 공공·행정 문서(공문·고지서·안내문)를 발달장애인·경계선지능인·고령자·이주민·저문해자가 이해할 수 있는 "쉬운 정보(Easy-Read)"로 변환하고, 그 쉬움(easiness)과 사실충실성(fidelity)을 기계가 측정·자가교정하는 오픈소스(Apache-2.0) 엔진**이다.

### 1.2 가치 제안
- **읽을 수 있는 게 아니라 이해할 수 있게.** WCAG·점자·TTS가 "지각 가능성(perceivable)"을 다룬다면, 또박은 "이해 가능성(understandable)" — 인지 접근성 — 을 다룬다.
- **측정 가능한 쉬움.** 한국 쉬운 정보 지침에 근거한 투명한 규칙 기반 K-ER 점수(0–100 + 규칙별 위반 목록)를 산출한다. 기존 한국어 가독성 도구(KReaD, 조용구 공식, EasyWord)는 *학년 수준(grade level)*을 재지만 *쉬운 정보 규칙 준수도*를 재지 않는다 — 이 점이 또박 지표의 새로움이다.
- **의미가 흐르지 않게.** 숫자·날짜·금액·기한·자격요건·기관명을 결정론적으로 대조하는 **Fidelity 게이트**가 왜곡을 자동 검출·롤백한다. 기존 솔루션은 사람이 감수하거나(온글) 점수만 매기는데(논문), 또박은 *자동 롤백*을 한다.
- **누구나 재사용.** 파이썬 코어 라이브러리 + 웹 데모 + MCP 서버, 전부 Apache-2.0. 지자체·개발자가 자가 호스팅·임베드·감사(audit) 가능. **단, 1인 8주 현실상 "코어 + 웹 데모"가 MVP 보장 2표면이고, MCP 서버는 권장 스트레치(3번째 표면, 'AI 에이전트' 주제 가산점)다 — 12·15절과 일관.**

### 1.3 자유과제(AI) 기술 임팩트
1. **에이전트형 자가교정 루프**: GENERATE→MEASURE→REVISE 루프가 규칙 위반 목록과 Fidelity 위반을 *재생성 제약(constraint)* 으로 되먹임. LLM provider-agnostic(Claude/GPT API 또는 로컬 Qwen2.5/Kanana).
2. **결정론 우선 + ML 보조의 사실충실성 검증기**: 정량 슬롯(숫자/날짜/금액)은 정규화 후 정확 일치, 조건·부정·범위는 NLI 단계 스택 — ML은 *플래그만* 올리고 *승인 권한은 없는* 신뢰 경로 설계.
3. **문헌 근거 기반 한국어 가독성 지표**: 조용구 검증 공식·장르별 독서지수·KcBERT 복잡도·RSRS·LLM-judge(LAURAE 신뢰도 가중)를 융합. 라벨 코퍼스 없이도 동작하는 비지도 앙상블.

### 1.4 왜 이기나 (심사 정합)
- **AI 기술 우수성**: 단순 LLM 호출이 아니라 측정→교정→롤백의 닫힌 루프. Fidelity 게이트가 헤드라인 AI 기여.
- **완성도**: 8–12개 실문서 end-to-end + 지표 수치(K-ER 델타, Fidelity recall) 정직 보고.
- **재사용 가능한 오픈소스 자산**: Apache-2.0 코드 + CC BY 데이터셋 + 3표면. 라이선스 검증 게이트를 통과하도록 설계.
- **사회적 임팩트 + 한국 적합성**: 「발달장애인 권리보장법」 제10조가 부과한 법적 의무를 직접 겨냥. **공공정보 중 쉬운 정보로 제공되는 비율은 1% 미만**(이큐포올·소소한소통·국민연금공단 NIA 컨소시엄 보도 — 웰페어뉴스/미디어생활 2025-07-21), 국가문해교육센터 2021 조사상 성인 약 20.1%가 낮은 문해력 — 이 격차를 메움.
- **정직성이 신뢰의 해자**: "한국어 쉬운 정보 AI 변환의 최초"라고 주장하지 않는다(온글·KCI 논문·KIPS 논문이 선행). "최초의 *열린·재현가능·포맷 네이티브* 한국어 Easy-Read *엔진*으로서 쉬움과 충실성을 *기계 측정·자가 교정*"이라고 주장한다.

---

## 2. 대상 사용자 & 사용 시나리오

### 2.1 최종 수혜자 (읽는 사람)
IFLA 가이드라인의 두 집단과 정확히 일치:
- **영속적 인지 지원 필요군**: 발달·지적 장애인, 경계선지능인, 학습장애.
- **일시적/제한적 읽기 능력군**: 고령자, 이주민·다문화, 저문해 성인, 신규 독자.

KEAD 2단계 모델을 따라 두 출력 등급을 지원:
- **보통 읽기(Plain Language)** — 국가문해교육센터 문해수준 3, 텍스트 중심.
- **쉬운 글(Easy Korean)** — 문해수준 1–2, 레이아웃·여백·그림 중심.

### 2.2 직접 사용자 (도구를 쓰는 사람)
- **공공기관 담당자**: 안내문/고지서를 쉬운 정보로 1차 변환 후 감수. (법 제10조 의무 이행)
- **장애인·복지 단체, 도서관**: 자료 제작 보조.
- **개발자/에이전트**: MCP 서버로 LLM 워크플로우에 인지 접근성 변환을 임베드.
- **연구자**: 공개 K-ER 지표·코퍼스로 한국어 Easy-Read 연구.

### 2.3 사용 시나리오 (대표 3)
1. **고지서 변환(머니샷)**: 건강보험료 고지서 PDF 투입 → 쉬운 글 변환. Fidelity 게이트가 LLM이 "1,295,400원"을 "약 130만 원"으로 반올림한 왜곡을 잡아 롤백 → 정확 금액·납부기한 보존. 원문/쉬운본 나란히 + "자동 변환 결과이며 원문이 우선합니다" 고지.
2. **정책 안내문 변환**: 청년 주거지원 안내문(공공누리 1유형) 투입 → K-ER 점수 42→81, 위반 목록(긴 문장 6건, 한자어 9건, 피동 3건)이 0건 근처로 감소하는 과정을 대시보드로 시연.
3. **에이전트 임베드(MCP)**: 외부 LLM 에이전트가 `ttobak.simplify(text, level="easy_korean")` 도구를 호출 → 쉬운본 + K-ER + Fidelity 리포트 JSON 수신.

---

## 3. 비기능 요구 / 원칙

### 3.1 Fidelity-first (최우선 원칙)
- 의미는 **절대** 흘러서는 안 된다. 쉬움과 충실성이 충돌하면 충실성이 이긴다.
- 출력은 **항상** 원문 + 면책 고지("자동 변환 결과, 원문 우선")와 함께 렌더링. Fidelity 게이트는 *방어층 중 하나*이지 유일한 안전망이 아니다.
- HIGH 중요도 슬롯(금액·기한·자격·부정·법적 의무·기관·연락처)은 정확 보존 실패 시 PASS 불가.

### 3.2 라이선스 클린
- 코드 = **Apache-2.0**(특허 grant 포함, 헤드라인 파서·Qwen2.5 가중치와 정합). 데이터셋 = **CC BY 4.0**. 픽토그램 = 각자의 CC BY-SA(별도 `/assets`).
- **5개 하드 블로커 회피**: pyhwp(AGPL), KoNLPy(GPL), Qwen2.5-3B/72B(NC/커스텀), EXAONE/Kanana-2-30B(NC/게이트), ARASAAC/KAAC(NC). (상세 9절)
- 출품 전 `pip-licenses` 의존성 스캔 + 시크릿/PII 부재 확인. 대회의 *별도* 라이선스·보안 검증 게이트를 1순위 통과 목표로.

### 3.3 재사용성
- 깨끗한 파이썬 코어 API 1개. 웹 데모·MCP 서버는 코어의 *얇은 래퍼*. 한 코드베이스로 2–3 표면.
- 기존 한국어 OSS 파서(hwp-hwpx-parser 등)를 *재사용·인용* — 파싱을 새로 만들지 않고 "한국 OSS 생태계 재사용 + 기여" 서사.

### 3.4 접근성
- 렌더러 자체가 KEAD/한국지적발달장애인복지협회 레이아웃 규칙 준수: ≥14pt(16pt+ 권장), 좌측 정렬, 한 줄 한 생각, 넉넉한 행간·여백(≥2.5cm), 그림은 설명 텍스트 옆, 페이지 번호·제공기관 정보.
- WCAG 대비·키보드 내비게이션 준수. 선택적 TTS(브라우저 Web Speech API, 무료).

---

## 4. 시스템 아키텍처

### 4.1 전체 데이터 흐름
```
[입력]  HWP/HWPX · PDF · 이미지 · 텍스트
   │
   ▼
┌─────────────────────────┐
│ A. 파싱·정규화 (Parse)   │  → 구조화 IR (Intermediate Representation)
└─────────────────────────┘
   │
   ▼
┌──────────────────────────────────────────────────────────┐
│ B. Easy-Read 파이프라인 (에이전트 루프)                     │
│    GENERATE ──▶ MEASURE ──▶ REVISE  (provider-agnostic LLM)│
│      ▲              │   │                                  │
│      │   ┌──────────┘   └──────────┐                       │
│      │   ▼                          ▼                       │
│      │  C. K-ER 지표             D. Fidelity 게이트          │
│      │  (0–100 + 위반목록)       (PASS/REVISE/HUMAN_REVIEW) │
│      └──────── 위반·위반슬롯을 재생성 제약으로 되먹임 ──────┘ │
└──────────────────────────────────────────────────────────┘
   │
   ▼
┌─────────────────────────┐   ┌─────────────────────────┐
│ E. 픽토그램 매칭         │   │ F. 렌더러 (side-by-side) │
│  (개념→Mulberry/OpenMoji)│──▶│  HTML · 쉬운 레이아웃 ·TTS│
└─────────────────────────┘   └─────────────────────────┘
   │
   ▼
[표면]  (1) 파이썬 패키지  (2) 웹 데모  (3) MCP 서버
```

### 4.2 모듈별 책임·인터페이스·의존

#### A. 파서·정규화 모듈 (`ttobak.parse`)
- **책임**: 다양한 입력을 단일 구조화 IR로. 미지원/깨진 입력은 *조용한 쓰레기*가 아니라 명시적 오류로 우아하게 저하(degrade).
- **인터페이스**: `parse(source: bytes|str|Path, mime: str) -> Document(IR)`
- **IR 스키마(Pydantic)**: `Document{blocks: [Block]}`, `Block{type: heading|paragraph|list_item|table|caption, text, level, spans, bbox?, confidence}`. 표는 `cells[][]`. 각 블록은 추출 신뢰도(OCR 등)를 보유.
- **의존**: hwp-hwpx-parser(HWPX, Apache-2.0), pypdf + pdfminer.six(PDF, BSD/MIT), pytesseract+Tesseract(OCR, Apache-2.0; 스트레치), Pillow/opencv-python-headless(이미지 전처리).

#### B. Easy-Read 파이프라인 (`ttobak.pipeline`)
- **책임**: IR을 받아 GENERATE→MEASURE→REVISE 루프 오케스트레이션. 출력 등급(보통읽기/쉬운글) 선택.
- **인터페이스**: `simplify(doc: Document, level: Level, provider: LLMProvider, max_revise: int=3) -> EasyReadResult`
- **`LLMProvider` 추상화**: `generate(prompt, schema?) -> str`. 구현: `AnthropicProvider`(데모 기본), `OpenAIProvider`, `OllamaProvider`(로컬, Kanana-1.5-8B / Qwen2.5-7B·14B).
- **루프 로직**: 정책 기반 LLM-as-a-Judge(arXiv 2512.06228) 방식으로 평행 코퍼스 없이 재생성. MEASURE에서 K-ER 위반 + Fidelity 위반 슬롯을 수집 → REVISE 프롬프트에 "반드시 '2026년 7월 17일'을 그대로 포함, 의역 금지" 같은 하드 제약으로 주입. 부정 플립은 자동 재생성 금지 → HUMAN_REVIEW.
- **의존**: C, D 모듈; LLM SDK(anthropic/openai/ollama).

#### C. K-ER 지표 모듈 (`ttobak.metric`)
- **책임**: 쉬움을 0–100 + 규칙별 위반 목록으로 산출. *충실성과 분리*(별개 숫자).
- **인터페이스**: `score(easy_text, source_text?, level) -> KERReport{score, sub_scores{}, violations: [Violation{rule, span, severity, suggestion}]}`
- **3계층 구성**(상세 5절): 규칙 기반 코어 + 모델 신호(KcBERT 복잡도·RSRS) + LLM-judge. LAURAE 신뢰도 가중 융합.
- **의존**: kiwipiepy(형태소, LGPL-3.0, 분리 의존), 그래프 easy-word 리스트, (선택)transformers·KcBERT.

#### D. Fidelity 게이트 (`ttobak.fidelity`)
- **책임**: (source IR, easy_text) 쌍에 대해 "의미가 흐르지 않았음"을 검증. PASS/REVISE/HUMAN_REVIEW 판정.
- **인터페이스**: `verify(source: Document, easy_text: str, ref_date: date) -> FidelityReport{slots:[...], verdict, exact_fail_count, nli_contradictions, drift_flags}`
- **구성**(상세 6절): SlotExtractor(규칙+NER+LLM) → SlotVerifier(정확 일치 + NLI + NegationGuard) → SemanticDriftMonitor(KoBERTScore, soft) → FidelityScorer&Router.
- **의존**: korean-number/es-hangul(수치 정규화), dateparser(Apache-2.0), pororo NER(Apache-2.0) 또는 spaCy ko, kf-deberta-base-cross-nli(NLI, MIT), KoBERTScore(soft).

#### E. 픽토그램 매칭 (`ttobak.pictogram`)
- **책임**: 쉬운본의 핵심 개념에 그림 짝짓기(이해 보조). *의미 일반 매칭이 아니라* 수작업 사전 룩업.
- **인터페이스**: `match(easy_text) -> [PictogramRef{concept, set, glyph_id, caption}]`
- **자산**: 수작업 큐레이션 ~150–300개 한국어 고빈도 개념 → Mulberry(CC BY-SA 2.0 UK)/OpenMoji(CC BY-SA 4.0) 글리프. 항상 한국어 캡션 병기.
- **의존**: `/assets/pictograms/` (코드와 분리, 자체 LICENSE).

#### F. 렌더러 (`ttobak.render`)
- **책임**: 원문/쉬운본 나란히 HTML + 쉬운 레이아웃 + 면책 고지 + K-ER 점수·Fidelity 상태 배지 + (선택)TTS.
- **인터페이스**: `render_html(result: EasyReadResult) -> str`
- **의존**: Jinja2 템플릿(또는 React/Svelte 웹 데모), jsdiff(diff 표시), Recharts(지표 대시보드).

#### 3개 표면
1. **파이썬 패키지(코어)**: `pip install ttobak`. 위 A–F 공개 API.
2. **웹 데모**: 동일 렌더러를 얇은 FastAPI/Gradio 페이지로 서빙(코어 재사용, 한계 비용 ~0).
3. **MCP 서버**: `mcp>=1.x,<2`(v2 alpha 회피). 도구 `simplify`, `score`, `verify_fidelity` 노출. 에이전트형/재사용 OSS 서사.

---

## 5. K-ER 지표 설계

### 5.1 문헌 근거 (라이브 검증 2026-06-30)
한국어 가독성 연구는 실재하나 얇다(KRIT 논문 자체가 "한국은 공개 데이터셋·자동 베이스라인이 거의 없다"고 명시). 인용 근거:

| 근거 | 핵심 | 출처 |
|---|---|---|
| 조용구, '글의 수준을 평가하는 국어 이독성 공식', 독서연구 41호(2016), 한국독서학회 | 공식 `학년수준 = 4.874 + 0.591×(평균 문장길이) − 9.201×(쉬운단어비율)³`, 쉬운단어비율 = 5,000 쉬운단어 목록 대비 %. **평균 문장 길이 + 쉬운/어려운 단어 비율이 가장 강한 한국어 가독성 예측인자.** (계수·지수 원문 verbatim 확인 2026-06-30; DOI 10.17095/JRR.2016.41.3) | https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART002171615 |
| 조용구 외, 'KReaD 지수 개발' (2020) | 28,332 단어를 10등급으로, 문장길이·난해어비율·문장구조점수·TTR·단문/복문비 출력. 전문가 판단·독해검사로 신뢰도 검증. | https://doi.org/10.37736/kjlr.2020.12.11.6.15 |
| KRIT (KAIST 2022) | 25,449 교과서 문장(8–16세, 4등급) 학습 BERT 기반 가독성 지수. 회귀 베이스라인 능가(acc 0.746, MAE 0.327). "공개 데이터셋·베이스라인 부재" 명시. | https://koasas.kaist.ac.kr/handle/10203/309526 |
| 장르별 독서지수 연구 | 도메인별 예측인자 상이: 인문/사회 = 내용어 총수, 어휘등급, 수식어 비율, 문장당 연결어미. 공공문서는 인문/사회/행정에 근접(R² ~0.558–0.698). | https://www.happycampus.com/paper-doc/31757264/ |
| RSRS (Martinc 2021) + biRSRS | 사전학습 LM 음의 로그우도/단어, 순위 √가중 + 문장길이. 비지도·라벨 불필요. 한국어 ESG 보고서에 zero-shot 적용됨. | https://github.com/guijinSON/Korean_Readability_Assessment |
| 나상수·김범진(2023), 응용언어학 39(3) | KcBERT 미세조정 한국어 문장 통사 복잡도 측정, NIKL 의존구문 코퍼스 acc 0.949. 설명가능성 위해 *요인별 서브모델* 주장. | https://www.dbpia.co.kr/journal/articleDetail?nodeId=NODE11527552 |
| LAURAE (ACL 2026) | `Score_final = c×LLM_std + (1−c)×Formula_std`, c = LLM 자기보고 신뢰도. 검증셋 튜닝 불필요(완전 비지도), 14개 중 13개 데이터셋 능가. CEFR 식 명시적 척도 앵커링이 보정 개선. | https://aclanthology.org/2026.acl-long.1832.pdf |
| LLM-judge 과신 현상 (arXiv 2508.06225) | verbal/CoT 신뢰도가 0.8–1.0에 몰리고 보정 불량. 다차원 'collective confidence'(차원별 독립 juror)가 더 신뢰. 소규모 보정셋 필요. | https://arxiv.org/pdf/2508.06225 |

권위 있는 한국 작성 지침(규칙의 출처): 국립국어원 '쉬운 공문서 쓰기 길잡이'(2022)·국어기본법 제14조; KEAD '알기 쉬운 자료 제작 안내서'(2021); 한국지적발달장애인복지협회/국립장애인도서관 안내서; Inclusion Europe 'Information for all'; IFLA 가이드라인 No.120. (URL은 11·15절 및 가이드라인 표 참조)

### 5.2 구성: 규칙 + 모델 + LLM-judge

**(1) 규칙 기반 K-ER 코어** (투명·고속·학습데이터 불필요). 각 규칙이 실제 지침에 매핑되며 0–100 서브점수 + 구체 위반 목록 산출(심사자·당사자 검토자가 감사 가능):

| 규칙 | 측정 | 근거 지침 | 방향 |
|---|---|---|---|
| 평균 문장 길이 | 어절/단어/음절 | 조용구 공식 (핵심) | 짧을수록 쉬움 |
| 난해어 비율 | 쉬운단어 목록 외 내용어 % | 조용구 5,000목록 / KReaD 등급 | 낮을수록 쉬움 |
| 한자어/외래어/외국문자 비율 | 토큰 분류 | KEAD·국립국어원 | 낮을수록 쉬움 |
| 문장당 서술어/연결어미 수 | 한 문장 한 생각 | KEAD, Inclusion Europe | >1 위반 |
| 피동 표현 비율 | 피동 접미사/구문 | Inclusion Europe r17, KEAD | 능동 선호 |
| 부정문 비율 | 부정 표현 | Inclusion Europe r16, KEAD | 긍정 선호 |
| 미정의 난해어 플래그 | 한자어/전문어가 정의·용어집 없이 등장 | KEAD(굵은 파랑+정의) | 위반 |
| 관용구/은유 플래그 | 관용구 사전 + LLM | Inclusion Europe r10, KEAD | 위반 |
| 약어/퍼센트/큰 숫자 플래그 | 미설명 % · 큰수 · 이니셜 | Inclusion Europe r12–13 | 위반 |
| 3인칭 대명사/가상인물명 플래그 | 그/그녀/가상명 | KEAD 특화(자기 매핑 실패) | 위반 |
| 직접 호명/행위주체 | 당신/여러분 존재, 주어 생략 회피 | KEAD(나/당신/우리) | 보상 |
| 수식어 비율·TTR/MATTR | 관형어·부사어, 어휘 다양성 | 장르 독서지수·KReaD | 과다 동의어 변주 벌점 |

**(2) 모델 신호** (규칙이 놓치는 것): KcBERT 미세조정 통사 복잡도 서브모델(NIKL 0.949), RSRS/biRSRS 비지도 '의외성' 점수. 둘 다 로컬·라벨 불필요. **[스트레치 — 일정 정직성] MVP K-ER은 규칙 기반 코어 + 선택적 off-the-shelf LLM-judge만 ship한다. KcBERT 미세조정 서브모델·RSRS/biRSRS는 다주 작업이라 12.3절 스트레치로 명시 연기(8주 1인 일정상 W3 미예산). 모델 신호 없이도 규칙 루브릭만으로 K-ER 핵심 가치 성립.**

**(3) LLM-judge** 전체 점수: *고정 척도* + 명시적 등급 정의(국가문해교육센터 문해수준 1/2/3에 앵커, CEFR식). 다차원 collective confidence(어휘/구조/전체 juror)로 과신 방어.

**융합**: LAURAE 신뢰도 가중 `Score = c×LLM_std + (1−c)×RuleModel_std`. 완전 비지도 → 대규모 라벨 코퍼스 없이 동작.

**보정(대규모 코퍼스 없이)**: 원본 공문 + 기존 공식 알기 쉬운 자료(KEAD/지자체 다수 공개)를 쉬움/어려움 앵커로 ~50–150개 페어링. *오직* LLM-judge 신뢰도 임계 설정·과신 탐지에만 사용.

### 5.3 산출물
`KERReport` = `{score: 0–100, level_estimate: 1|2|3, sub_scores: {rule, model, llm}, violations: [{rule, span, severity(HIGH/MED/LOW), suggestion}]}`. 위반 목록은 발달장애인 가독성 가이드라인 분류(내용 = 어휘/문장/조직/삽화, 형식 = 텍스트/레이아웃/디자인; Delphi 검증 KCI ART002440711)에 따라 그룹화.

> **정직성 프레이밍(필수) + 산출 결정(고정)**: K-ER은 *공개·검증된 한국어 Easy-Read 라벨 코퍼스가 없으므로* 8/27까지 *경험적으로 검증 불가*. **결정: 0–100 점수와 규칙별 위반 체크리스트를 *항상 함께* 산출한다. 체크리스트(pass/fail)가 하중 지지(load-bearing) 산출물이고, 0–100 숫자는 "비검증 보조 지표(non-validated auxiliary)"로 명시 라벨한다 — 런타임 조건부 격하/분기는 두지 않는다(구현·심사 모호성 제거).** "한국 Easy-Read 지침 정렬 규칙 기반 루브릭, 경험적 검증 아님"을 문서·영상·UI 모든 표면에 명시.

---

## 6. Fidelity 게이트 설계

### 6.1 설계 철학: 결정론 우선, ML 보조
숫자/날짜/금액/기한은 정규화 후 **정확·규칙 기반 일치**(무관용, 신뢰 경로에 LLM 없음). 조건/자격/부정/범위는 **단계 시맨틱 스택**(규칙 휴리스틱 → NLI → 선택 LLM-judge)으로 검증하되 ML은 *플래그만 올리고 승인하지 않음*. 게이트는 (source IR, easy_text) 쌍에 대한 분류기로 `FidelityReport` + 3판정(PASS/REVISE/HUMAN_REVIEW) 산출. 핵심 메커니즘 = **슬롯 생존(slot survival)**.

### 6.2 파이프라인
```
Source IR ──▶ [1] 슬롯 추출 (규칙 + NER + LLM)  → 타입화 보존필수 fact 슬롯
Easy-Read ──▶ [2] 슬롯 검증
                  ├─ 정확일치 : NUMERIC/DATE/MONEY/DURATION/CONTACT/ENTITY
                  ├─ NLI(양방향): CONDITION/ELIGIBILITY/MODALITY/SCOPE
                  └─ NegationGuard: 명시적 극성 페어링
           ──▶ [3] 시맨틱 드리프트 모니터 (KoBERTScore, soft flag only)
           ──▶ [4] FidelityScorer + Router → PASS / REVISE / HUMAN_REVIEW
```

### 6.3 슬롯 추출 (보존 필수 fact)
타입: NUMERIC · DATE/DEADLINE · MONEY(KRW, 만/억/조) · DURATION/PERIOD · ELIGIBILITY/CONDITION · AGENCY/ORG · CONTACT(전화/주소/URL) · PERSON/ENTITY · **NEGATION**(제외·아님·불가·없음) · **CONDITIONAL**(~경우·~하면·~한 자에 한해) · MODALITY/OBLIGATION(해야 한다 vs 할 수 있다) · QUANTIFIER/SCOPE(모든·일부·이상·이하·초과·미만·까지·부터).
각 슬롯: `{raw_span, normalized_value, type, polarity, source_offset, criticality(HIGH/MED/LOW)}`. 추출은 redundant — regex ∪ NER ∪ LLM. 소스 추출 신뢰도 낮으면 전체 문서를 HUMAN_REVIEW.

### 6.4 슬롯 검증
- **NUMERIC/DATE/MONEY/DURATION/CONTACT**: 양측을 정규형(int/Decimal KRW/ISO-8601/정규화 전화)으로 변환, *정확 일치* 요구. 누락·추가·변경 = 왜곡. 경계어(이상=≥, 초과=>, 이하=≤, 미만=<, 까지=inclusive)는 값의 일부로 검사 — 생성기가 `미만`을 `이하`로 약화 불가.
- **ENTITY/AGENCY/PERSON**: 정확 또는 별칭 정규화 일치(강서구청 == 서울특별시 강서구청). 소스에 없는 새 엔티티 = 환각.
- **NEGATION/CONDITIONAL/MODALITY/SCOPE**: 시맨틱. 각 소스 조건을 가설로, easy_text가 그것을 entail하고 부정은 entail하지 않는지 양방향 NLI(소스→출력 "추가/변경된 의미", 출력→소스 "지지").

### 6.5 의미 등가 계층(전역)
슬롯 없는 의역 드리프트 검출: 문장 정렬 NLI(SummaC식: 문장 분할, max-entailment 정렬, 소스 단위 min) + KoBERTScore(soft 보조). NLI가 모순 검출의 권위. KoBERTScore는 *의심스러운 저유사도만 플래그*(승인엔 미사용 — 높은 임베딩 유사도가 부정 플립을 가릴 수 있으므로).

### 6.6 검증 컴포넌트 (라이브 검증·라이선스 클린)

| 계층 | 컴포넌트 | 라이선스 | 비고 |
|---|---|---|---|
| 한글 수↔숫자 | korean-number / es-hangul(Toss) | open | `kor2num('삼만원')→30000`; '3만5천원','약 3억 원' 처리 |
| 날짜 파싱(절대+상대) | dateparser | Apache-2.0 | ko 로케일; PR #1289(2026-06-09) 한국어 날짜표현 추가 |
| NER(주) | spaCy ko_core_news_lg | CC BY-SA 4.0 | DT/LC/OG/PS/QT/TI; 유지·설치 안정 → **기본 NER** |
| NER(폴백) | pororo (kakaobrain) | Apache-2.0(코드) | KLUE F1 89.63이나 **archived + 무거운 고정 의존(구 torch/fairseq era) → caution(패키징·보안 게이트 위험). 문서화된 폴백만, 기본 채택 X** |
| **NLI(조건/부정)** | deliciouscat/kf-deberta-base-cross-nli | **MIT** | 0.2B, KorNLI+KLUE-NLI, KLUE-NLI acc 0.8897; base kakaobank/kf-deberta-base MIT |
| 시맨틱 드리프트(soft) | lovit/KoBERTScore 또는 metterian/korean_bert_score | open(PyPI 미배포; git vendor) | KorSTS corr 0.62(kcbert)/0.663(klue-roberta-large) |

> NLI 학습 데이터(KorNLI/KLUE-NLI)는 CC BY-SA 4.0 — 추론·가중치 재배포는 무방(모델 자체 MIT). 라이선스 리포트에 데이터셋 라이선스 명기.

### 6.7 NegationGuard (전용)
NLI/임베딩이 단일 토큰 부정 플립을 자주 놓치므로 전용 규칙: 제외/아니/불가/없/금지/말/~지 않 패턴 스캔, 각 소스 부정을 동일 슬롯의 출력 부정과 페어링. 소스가 X를 부정하는데 출력이 X를 단언/부정 누락 → 하드 실패 → HUMAN_REVIEW(자동 재생성 금지, 너무 위험).

### 6.8 임계 & 라우팅
- **PASS**: 모든 HIGH 슬롯 정확 생존 + NLI 모순 없음 + 부정 플립 없음.
- **REVISE**(자동 루프, max N≈2–3): 복구 가능한 정확일치 실패(숫자 누락/왜곡, 날짜 의역, 정밀값에 헤지 추가). 실패 슬롯을 "반드시 verbatim, 의역 금지" 제약으로 주입 후 재게이트.
- **HUMAN_REVIEW**: (a) 부정/조건 극성 플립, (b) 국소화 불가 NLI 모순, (c) 소스 대응 없는 환각 슬롯, (d) N루프 후 잔존 실패, (e) 소스 추출 저신뢰. '검수 필요' 배너로 보류/표시.
- **수치 임계**: numeric/date/money 허용오차 0(정확 일치). **반올림 예외(엄밀 정의): allowlist는 기본 비어 있고 슬롯 단위 opt-in. 반올림 출력이 PASS가 되려면 세 조건 동시 충족 — (1) 소스 스팬에 헤지 토큰(약/대략/여/내외)이 문자 그대로 존재 AND (2) 출력이 동일 헤지 토큰을 보존 AND (3) 해당 슬롯이 문서 단위 allowlist에 등재. 하나라도 불충족 = 왜곡 처리.** (14.1절 단위 테스트로 고정.) NLI 조건당 entailment ≥0.7 & contradiction <0.1 양방향, HIGH 슬롯 contradiction ≥0.5 = 하드 실패. KoBERTScore 드리프트 = advisory only.

### 6.9 게이트 자체 평가법 (대회 산출물)
**주입형 왜곡 벤치마크**: 알려진 충실 (source, easy) 페어에서 easy 측을 타입별로 프로그래밍 변조 — 숫자 교환(30,000→3,000), 자릿수 누락, KRW 단위 오류(3억→3천만), 날짜 이동(7/17→7/7), 포함성 플립(까지→전에), 부정 누락(제외→포함), 조건 플립(만65세 이상→이하), 범위 약화(미만→이하), 기관 교환, 환각 엔티티, + clean control. 측정:
- 타입별 recall + 타입 국소화 혼동행렬
- distorted-vs-clean 전체 precision/recall/F1, clean control의 FP율(과플래그 비용)
- 컴포넌트 ablation(rules-only → +NLI → +LLM-judge)
- 정규화기 단위테스트('약 3억 원'→300000000, '2026년 7월 17일까지'→ISO+inclusive) recall 1.0 목표
- **PASS 출력의 잔존 왜곡율** — 가장 중요한 숫자, HIGH 슬롯에서 ~0 목표

**자체 품질 목표**: HIGH 슬롯 왜곡 recall ≥0.95, precision ≥0.85, 정확일치기 recall =1.0. (재현율 우선 — 진짜 왜곡을 놓치는 게 거짓경보보다 나쁨; fail-safe = '검수 필요'가 무성 의미드리프트보다 낫다.)

### 6.10 실패 모드
1. **부정 누락/플립**(제외→포함) — 임베딩은 높게 유지, 의미 반전 → NegationGuard + 양방향 NLI → HUMAN_REVIEW.
2. **조건/범위 플립**(이상→이하, 미만→이하) — 경계어 테이블 + NLI.
3. **반올림 금액**(1,295,400원→약 130만 원) — 무관용 matcher; 반올림은 헤지+allowlist 시에만.
4. **날짜 드리프트/포함성 변경** — dateparser `RELATIVE_BASE`=문서일 + inclusive-flag.
5. **추출기 자체 정규화 버그**('삼천오백만', '3만5천', 억/조 혼동) — 단위테스트 + 이중 라이브러리 교차검증, 불일치 → human.
6. **환각 엔티티/숫자** — 모든 출력 슬롯이 소스로 역매핑 필수; orphan = 환각.
7. **양상 드리프트**(해야 한다→하면 된다) — MODALITY 슬롯 + NLI.
8. **NLI 과신**(관료 문체·긴 전제 약함) — 문장 분할 + SummaC 집계, 도메인 dev셋 보정, 정량은 규칙이 권위.
9. **과플래그 → 무한 루프** — N 제한 후 human, criticality 가중.
10. **소스 추출 누락**(silent gap) — redundant 추출, 저신뢰 시 전체 문서 human, 추출 커버리지를 지표로 보고.
11. **상류 IR 오류**(OCR/HWP 숫자 깨짐)가 '잘못된 소스에 충실'로 전파 — 게이트 범위 밖이나 저신뢰 영역 플래그, 렌더러가 항상 원문+면책 표시.

> **MVP 컷(타당성)**: 신뢰도 우선순위가 빠듯하면 NUMERIC+DATE+AMOUNT+DEADLINE만(자격/엔티티 시맨틱은 스트레치). 정확한 수치/날짜/금액 가드만으로도 설득력 있고 시연 가능한 사회적 결과.

### 6.11 출처
korean-number(https://pypi.org/project/korean-number/) · es-hangul(https://pypi.org/project/es-hangul/) · dateparser(https://github.com/scrapinghub/dateparser) · pororo(https://github.com/kakaobrain/pororo) · spaCy ko(https://huggingface.co/spacy/ko_core_news_lg) · kf-deberta-base-cross-nli(https://huggingface.co/deliciouscat/kf-deberta-base-cross-nli) · KoBERTScore(https://github.com/lovit/KoBERTScore) · 충실성 방법론: SummaC(arXiv 2111.09525), QAGS(ACL 2020), FEQA(arXiv 2005.03754), FENICE(ACL Findings 2024).

---

## 7. 입력 파서

### 7.1 입력 티어링 (타당성 반영: 텍스트/PDF 우선, HWPX best-effort, OCR 스트레치)

| 형식 | 채택 라이브러리 | 라이선스 | 출처 | 우선순위 |
|---|---|---|---|---|
| 텍스트 | (내장) | — | — | PRIMARY(신뢰) |
| PDF 텍스트/레이아웃 | pypdf | BSD-3-Clause | https://pypi.org/project/pypdf/ | PRIMARY |
| PDF 마이닝(보완) | pdfminer.six | MIT | https://pypi.org/project/pdfminer.six/ | PRIMARY |
| HWP/HWPX | **hwp-hwpx-parser** | **Apache-2.0** | https://pypi.org/project/hwp-hwpx-parser/ | BEST-EFFORT(HWPX 우선) |
| OCR 엔진 | Tesseract | Apache-2.0 | https://github.com/tesseract-ocr/tesseract | STRETCH |
| OCR 바인딩 | pytesseract | Apache-2.0 | https://pypi.org/project/pytesseract/ | STRETCH |
| 이미지 처리 | opencv-python-**headless** / Pillow | Apache-2.0(코어)/MIT | https://github.com/opencv/opencv-python | STRETCH |

### 7.2 라이선스/회피 노트
- **pyhwp = AGPL-3.0 (블로커)**: 네트워크 카피레프트가 엔진+웹+MCP를 AGPL로 전염. import/link/vendor 금지. hwp-hwpx-parser 사용. (https://pypi.org/project/pyhwp/)
- hwp-hwpx-parser: 순수 파이썬, v1.0.0. **런타임 의존 = olefile(BSD) + python-docx(MIT) — 둘 다 permissive(라이브 확인 2026-06-30 PyPI 메타데이터; 이전 초안의 'olefile만'은 오기 정정).** 신규·1인 프로젝트이므로 버전 핀 + 출품 전 `pip show`로 전이 의존 트리 재확인 + 폴백 유지. "Apache + 순수파이썬"이 *추출 품질*을 보장하진 않음 — 복잡 표·다단 레이아웃·legacy .hwp 바이너리는 best-effort, 깨끗이 파싱되는 데모 문서를 큐레이션.
- **대안(문서화)**: kordoc(npm, MIT; HWP3/5/HWPX/PDF/XLSX/DOCX→MD)·dochan(Python, MIT). Node이므로 파이썬 코어에선 서브프로세스/HTTP 경계로 웹/MCP 표면에 활용 가능. 파싱을 새로 만들지 않고 *재사용·인용*.
- opencv: prebuilt wheel이 FFmpeg(LGPLv2.1, 모든 wheel)·Qt5(LGPLv3, 비headless Linux) 번들. **opencv-python-headless 사용(Qt5 회피) + FFmpeg LGPL 고지**, 또는 기본 연산은 Pillow.

### 7.3 우아한 저하
미지원/깨진 입력 → 명시 오류 + 블록 신뢰도 표기. OCR 저신뢰 영역은 렌더러가 원문 병기로 사람이 검증 가능하게.

---

## 8. 공개 코퍼스 계획

### 8.1 목표
**ship 목표(8/27) = 8–12개 완전 주석 source→easy-read 페어**(각 K-ER 점수 + 필드별 Fidelity 주석 + 프로비넌스 로그 — 12절 MVP·14.4절 평가 n과 일치). **100–300개 확장은 대회 이후 로드맵**으로 명시(데이터셋 카드의 약속 n = 실제 평가 보고 n). GitHub/HuggingFace에 클린 라이선스로 공개, 대회 라이선스 게이트 통과.

### 8.2 출처 선택 (재배포 가능한 것만)

**허용**:
- **공공누리 제1유형(출처표시)** 문서만 — 문서별 Type-1 마크 확인. 상업+수정+재배포 허용, 출처표시 의무. (https://www.kogl.or.kr/info/licenseType1.do)
- data.go.kr 데이터셋 중 이용허락범위 = CC BY 또는 '제한없음'.
- 우리가 직접 저작한 쉬운본/합성 소스(저작권 보유 → 자유 재라이선스).

**제외(공개 코퍼스에서)**:
- **AI Hub** — 재가공 배포 원칙적 불가, 원본 국외반출 금지, 미승인 제3자 제공 금지. GitHub 공개 = 국외 배포 → 금지. (사적 학습/평가만 가능; 산출 모델/서비스는 배포 가능) (https://aihub.or.kr/intrcn/guid/usagepolicy.do)
- **국립국어원 모두의 말뭉치** — IP는 NIKL, 무단 복제/재배포/상업 금지, 산출 결과에 소스 텍스트 포함 불가 + 사전승인 필요. 사적 dev/참조만. (https://kli.korean.go.kr/m/introduce/termsInfo.do)
- ARASAAC/KAAC 픽토그램(NC), KOGL Type-2/3/4, CC-NC 소스, 실제 PII 포함 문서.

### 8.3 페어 제작
- **소스 측**: KOGL-1 원문(verbatim + 전체 출처표시) 또는 원본이 재배포 불가면 우리 합성/의역 소스. (사실 — 숫자·날짜·금액 — 은 저작권 대상 아님이나 *원문 표현/레이아웃*은 저작권 대상.)
- **쉬운 측**: GENERATE→MEASURE→REVISE 루프 생성 후 사람 편집. 우리 저작 → CC BY/CC0 선택.
- **저장 필드**: `source_text, easy_text, source_license{type,attribution,url,date_fetched}, kER_score, kER_rule_violations[], fidelity_checks{numbers,dates,amounts,deadlines,eligibility,entities: preserved?, distortions[]}, pictogram_refs[]{set,glyph_id,modified}, reviewer, review_date`.

### 8.4 검토 프로세스 (2-pass)
(1) 자동 Fidelity 게이트(모든 숫자/날짜/금액/기한/자격/엔티티가 쉬운본에 설명되어야 함, 드리프트 없음). (2) 사람 검토자(1인 solo; 검토자+날짜 로깅) 가독성 + PII/저작 표현 누출 점검. 출처 프로비넌스 로그(CSV/JSONL)에 URL·수집일·KOGL 유형 증거 기록 → 라이선스 게이트 감사 가능.

### 8.5 공개 방식 & 디렉터리
```
/corpus/
  pairs.jsonl              # 데이터셋 (CC BY 4.0)
  DATA_LICENSE             # 주석/쉬운본용 CC BY 4.0
  SOURCES.csv             # 출처별: 제목,기관,연도,url,KOGL유형,수집일
  NOTICE-sources.md       # KOGL-1 출처표시 블록(마크 이미지 아님, 텍스트)
/assets/pictograms/
  mulberry/  (unmodified)  LICENSE=CC BY-SA 2.0 UK + ATTRIBUTION.md
  openmoji/  (unmodified)  LICENSE=CC BY-SA 4.0 + ATTRIBUTION.md
  derived/   (our edits)   LICENSE=CC BY-SA(소스셋 버전 일치) + CHANGES.md
/  LICENSE (Apache-2.0, 코드)
   NOTICE (3rd-party 출처표시 집약)
   THIRD_PARTY_LICENSES.md
   DATASET_CARD.md (프로비넌스, 제외, PII 처리, 의도된 용도, 면책)
/dev-only/  (gitignored)  # AI Hub·모두의 말뭉치·NC/PII = 사적 평가 전용, 미배포
```

### 8.6 의무 출처표시 (drop-in)
- **KOGL-1**: "본 저작물은 '<기관명>'에서 '<연도>' 작성하여 공공누리 제1유형으로 개방한 '<저작물명>'을 이용하였으며, 해당 저작물은 '<기관명>, <누리집 URL>'에서 무료로 내려받으실 수 있습니다." + 하이퍼링크. (사용자는 마크 이미지 부착 금지 — 발급기관만 가능; 텍스트형 사용)
- **OpenMoji**: "All emojis designed by OpenMoji – the open-source emoji and icon project. License: CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/)". 수정 시 명기.
- **Mulberry**: "Mulberry Symbols are copyright 2018 to 2026 Steve Lee and licensed under CC BY-SA 2.0 UK: England & Wales. See https://mulberrysymbols.org". 수정 시 명기.

### 8.7 면책 (Fidelity-first)
모든 공개 페어 + 렌더러는 원문 + "쉬운본은 보조 자료이며 법적 효력은 원문이 우선합니다" 면책을 유지.

> **타당성 폴백**: 실문서 수집이 막히면 합성-사실적 고지서/안내문을 직접 저작(명확히 '합성' 라벨)해 파이프라인+게이트를 end-to-end 시연. 실측 n=5가 약속된 n=100보다 낫다.

---

## 9. 라이선스 매트릭스

전 의존성 라이브 검증 2026-06-30 (PyPI/GitHub/HuggingFace/프로젝트 사이트). 위험: clean(클린) / caution(주의-패키징) / blocker(블로커).

### 9.1 코드 의존성

| 컴포넌트 | 채택 | 라이선스 | 위험 | 출처 |
|---|---|---|---|---|
| HWP/HWPX 파서 | hwp-hwpx-parser | Apache-2.0 | clean | https://pypi.org/project/hwp-hwpx-parser/ |
| ↳ 파서 런타임 의존 | olefile + python-docx | BSD-2 / MIT | clean | https://pypi.org/project/python-docx/ |
| PDF 텍스트 | pypdf | BSD-3-Clause | clean | https://pypi.org/project/pypdf/ |
| PDF 마이닝 | pdfminer.six | MIT | clean | https://pypi.org/project/pdfminer.six/ |
| OCR 엔진 | Tesseract | Apache-2.0 | clean | https://github.com/tesseract-ocr/tesseract |
| OCR 바인딩 | pytesseract | Apache-2.0 | clean | https://pypi.org/project/pytesseract/ |
| 이미지 처리 | opencv-python-headless | Apache-2.0(코어)/MIT(wrapper) | caution(FFmpeg LGPL 번들) | https://github.com/opencv/opencv-python |
| 형태소 분석(권장) | **kiwipiepy(Kiwi)** | LGPL-3.0 | caution(분리 의존으로 OK) | https://pypi.org/project/kiwipiepy/ |
| 형태소(대안) | soynlp | LGPL-3.0 | caution | https://github.com/lovit/soynlp |
| 형태소(대안, Apache) | Khaiii(Kakao) | Apache-2.0 | caution(2019 이후 미유지) | https://github.com/kakao/khaiii |
| 형태소(MeCab 경로) | pymecab-ko + mecab-ko-dic | 엔진 tri(BSD 선택)/사전 Apache-2.0 | caution(GPL 오태깅 함정) | https://pypi.org/project/mecab-ko/ |
| 시맨틱 유사도 | bert-score | MIT(가중치 별도) | clean | https://pypi.org/project/bert-score/ |
| 임베딩 | sentence-transformers | Apache-2.0(가중치 별도) | clean | https://pypi.org/project/sentence-transformers/ |
| 트랜스포머 프레임워크 | HF transformers | Apache-2.0 | clean | https://github.com/huggingface/transformers |
| NLI(Fidelity) | kf-deberta-base-cross-nli | MIT | clean | https://huggingface.co/deliciouscat/kf-deberta-base-cross-nli |
| 한글 수치 정규화 | korean-number / es-hangul | open(permissive) | clean | https://pypi.org/project/korean-number/ |
| 날짜 파싱 | dateparser | Apache-2.0 | clean | https://github.com/scrapinghub/dateparser |
| NER(주/폴백) | spaCy ko_core_news_lg / pororo | CC BY-SA 4.0(자산) / Apache-2.0(코드) | clean / **caution(pororo archived·무거운 고정의존)** | https://huggingface.co/spacy/ko_core_news_lg |
| 웹 API | FastAPI | MIT | clean | https://github.com/fastapi/fastapi |
| ASGI 서버 | Uvicorn | BSD-3-Clause | clean | https://github.com/encode/uvicorn |
| 데이터 검증 | Pydantic | MIT | clean | https://github.com/pydantic/pydantic |
| 프론트엔드 | React / Svelte | MIT | clean | https://github.com/facebook/react |
| 차트 | Recharts / Chart.js | MIT | clean | https://github.com/recharts/recharts |
| diff | jsdiff / diff-match-patch | BSD-3-Clause / Apache-2.0 | clean | https://www.npmjs.com/package/diff-match-patch |
| MCP SDK | mcp(python-sdk) | MIT | clean(`>=1.x,<2` 핀) | https://github.com/modelcontextprotocol/python-sdk |
| 로컬 LLM 런타임 | Ollama | MIT | clean | https://github.com/ollama/ollama |

### 9.2 모델 가중치

| 모델 | 라이선스 | 위험 | 출처 |
|---|---|---|---|
| **Qwen2.5 — 0.5B/1.5B/7B/14B/32B** | Apache-2.0 | clean(7B/14B 권장) | https://huggingface.co/Qwen/Qwen2.5-7B-Instruct |
| Qwen2.5 — 3B / 72B | 3B: Qwen RESEARCH(NC) / 72B: 커스텀(>100M MAU) | **blocker** | https://huggingface.co/Qwen/Qwen2.5-3B-Instruct/blob/main/LICENSE |
| **Kanana 1.5 — 8B / 2.1B (Kakao)** | Apache-2.0 | clean(한국어 강함, 로컬 폴백 권장) | kakaocorp.com 2025-05-23 / HF kanana-1.5-2.1b-base |
| Kanana 2 — 30B | 별도 Kanana License(상업 API/MAU 게이트) | blocker(shipped 경로 제외) | — |
| EXAONE 3.5/4.0 (LG) | EXAONE AI Model License — NC | blocker(**제출 산출물 — 레포·데모·영상 — 에서 전면 배제. "쓰지 않은 알려진 NC 대안"으로만 문서화** — 비상업 맥락 carve-out 두지 않음) | https://github.com/LG-AI-EXAONE/EXAONE-3.5/blob/main/LICENSE |

### 9.3 픽토그램 자산 (코드와 분리, `/assets`)

| 세트 | 라이선스 | 위험 | 출처 |
|---|---|---|---|
| Mulberry Symbols(주) | CC BY-SA 2.0 UK | caution(SA, 상업OK; 미유지 플래그) | https://mulberrysymbols.org/ |
| OpenMoji(보조) | CC BY-SA 4.0 | caution(SA, 상업OK) | https://openmoji.org/faq/ |
| ARASAAC / KAAC | CC BY-NC-SA / NC | **blocker** | https://arasaac.org/ |

### 9.4 프로젝트 라이선스 결정
- **코드 = Apache-2.0** (Python 코어·웹·MCP). 근거: (1) ship하는 모든 코드 의존성이 permissive(Apache/MIT/BSD) 또는 분리형 weak-copyleft(LGPL: kiwipiepy/soynlp), Apache 배포와 호환; (2) Apache의 명시적 특허 grant가 기관 후원 대회·다운스트림 재사용에 유리하고 헤드라인 파서·Qwen2.5 가중치와 NOTICE 정합; (3) '재사용 가능한 오픈소스 자산' 심사 점수 극대화.
- **데이터셋 = CC BY 4.0**(또는 최대 재사용 원하면 CC0).
- **픽토그램 = 각자의 CC BY-SA**(별도 `/assets`, Apache로 재라이선스 안 함). SA on 자산은 Apache 코드를 전염 안 함(별개 저작물; mere aggregation). 단 *수정*한 글리프는 동일 CC BY-SA 유지. 근거: CC ShareAlike-interpretation wiki, OpenMoji issue #462(maintainer: "No, you don't have to release the entirety"), opensource.stackexchange.
- **임베드 규칙(검증 게이트 대비)**: 렌더러는 픽토그램을 **파일 경로/URL 참조로만** 사용한다. *수정된* CC BY-SA 글리프를 Apache 코드 산출물이나 CC BY 데이터셋 출력에 **인라인/base64로 내장하지 않는다**(결합저작물 생성 회피). 수정 글리프(`/assets/pictograms/derived/`)는 **별도 라이선스 자산 팩**으로 ship.

### 9.5 회피한 카피레프트/NC (요약)
- **AGPL**: pyhwp → hwp-hwpx-parser로 대체.
- **GPL**: KoNLPy(+래핑 GPL 엔진) → kiwipiepy(LGPL, 비-GPL, 분리)로 대체.
- **NC/커스텀 모델**: Qwen2.5-3B/72B, Kanana-2-30B, EXAONE → Apache 사이즈(Qwen2.5-7B/14B/32B, Kanana-1.5-8B/2.1B)로.
- **NC 픽토그램**: ARASAAC/KAAC → Mulberry/OpenMoji(CC BY-SA, 상업OK)로.

### 9.6 패키징 액션(라이선스/보안 게이트)
1. top-level `LICENSE`=Apache-2.0 + `NOTICE`(Apache 출처표시 + Qwen NOTICE 집약).
2. 핀: `mcp>=1.27,<2`(상류 README 권장; v2 stable 목표 ~2026-07-27, alpha 이미 배포 중 → 안정 v1.x 고수), hwp-hwpx-parser(신규/1인), opencv-python-headless(Qt5 회피; FFmpeg LGPLv2.1 번들 고지) 또는 기본 연산 Pillow.
3. kiwipiepy/soynlp LGPL relink 노트 + "소스 미수정" 입장 문서화.
4. 데이터셋 CC BY 4.0/CC0; 픽토그램 `/assets` 각자 CC BY-SA.
5. 모델 가중치를 ship하거나 72B/EXAONE 포함 시 라이선스 텍스트 + 필수 고지("Built with Qwen" 등) verbatim 동봉.

---

## 10. 경쟁 지형 & 차별화 포지셔닝

> **레드팀 평결(정직)**: 웻지(wedge)는 *여전히 열려 있으나 가정보다 좁고 방어적 포지셔닝이 필요*하다. 살아있는 정부 후원 상업 인큐번트(온글)를 *반드시 명명·정면 대응*. 또박의 새로움은 *한국어 Easy-Read AI 변환 최초*가 아니라 *최초의 열린·측정가능·자가교정·포맷네이티브 엔진*이다. (모든 사실 라이브 검증 2026-06-30)

### 10.1 위협 순위

| # | 인큐번트 | 위협 | 이미 하는 것 | 안 하는 것(우리 갭) |
|---|---|---|---|---|
| 1 | **온글(EQ4ALL+소소한소통)** [link](https://www.eq4all.co.kr/ongl) | 🔴 CRITICAL | LIVE SaaS(서비스 2026-05-21). 정확히 우리 도메인: 초거대-AI 쉬운정보 변환(발달장애인·고령자·외국인). **NIA 'AI·애자일 혁신서비스' 사업으로 개발 — EQ4ALL 주관(AI모델·서비스), 소소한소통 학습데이터, 국민연금공단 공공정보 실증**(웰페어뉴스/미디어생활 2025-07-21). 사람 전문가+당사자 감수. RAG 기관별. 웹 '쉬운 글 보기' 오버레이. | 폐쇄 SaaS, 라이선스/GitHub/MCP/API-score 없음. 공개 0–100 지표 없음. HWP/PDF/OCR 파이프라인 없음. 자동 Fidelity 롤백 없음(사람). 픽토그램 없음. |
| 2 | **KCI 2025 논문**(보인정보기술/숙명여대) [link](https://www.kci.go.kr/kciportal/ci/sereArticleSearch/ciSereArtiView.kci?sereArticleSearchBean.artiId=ART003240933) | 🔴 HIGH | 발달장애인 LLM Easy-Read 생성+평가; 28 정량+10 정성 요소; 19 당사자+9 전문가 검증. "DD검증 루브릭 신규" 주장 선점. | 논문(미공개 OSS). 에이전트 루프·롤백 게이트·포맷/픽토그램/MCP 없음. |
| 3 | **KIPS ACK 2024**(동국대) [link](https://www.manuscriptlink.com/society/kips/conference/ack2024/file/downloadSoConfManuscript/abs/KIPS_C2024B0060) | 🟠 HIGH | 한국어 이지리드 평가: 가독성(SC, GFI, GPT-4o RS) + 충실성(KoBERTScore). 코드+데이터 공개. 가독성/충실성 트레이드오프. | 벤치마크만. 일반 GFI/SC(한국 Easy-Read 규칙 점수 아님). 엔진/루프/롤백/포맷/MCP 없음. |
| 4 | **WIA 글살림**(MIT) [link](https://github.com/WIA-Official/wia-geulsalim) | 🟠 MEDIUM(동일 대회) | 시끄러운 2026 대회 파이프라인: 고문서 복원 + WCAG/EPUB 구조 + 점자/TTS/3D수어/WebXR. 특허·마케팅. | **감각** 접근(시각/청각), **인지** 아님. 쉬운말 재작성·Easy-Read 점수·Fidelity 게이트·픽토그램 이해보조·HWP 인지단순화·MCP 없음. |
| 5 | **kordoc / hwp-mcp / GongMun-Doctor / hwpx-mcp** [link](https://github.com/sinmb79/GongMun-Doctor-MCP) | 🟡 INFRA | 한국문서 파싱+MCP 이미 소유: HWP/HWPX/PDF→MD, 폼필, diff, write, OCR, provider-agnostic LLM, 템플릿. | 전부 공무원 교정/생성용 — 인지 Easy-Read·Easy-Read 점수·Fidelity 게이트·픽토그램 없음. → **재사용, 재구축 금지.** |

### 10.2 방어 가능한 새로움 (유일한 정직한 주장)
어떤 프로젝트도 **6가지 전부**를 결합하지 못함: (a) 열린 규칙 기반 **한국어 Easy-Read 점수**(0–100 + 규칙별 위반, 국립장애인도서관/소소한소통/URP 지침 근거 — 기존 KR 도구 KReaD/조용구 공식은 *학년*만 측정), (b) 자동 **Fidelity 롤백 게이트**, (c) 에이전트 **generate→measure→revise** 루프, (d) 픽토그램, (e) HWP/HWPX/PDF/OCR 수집, (f) **MCP**, **Apache-2.0** ship.

→ 주장: *"쉬움과 충실성을 기계 측정·자가 교정하는 최초의 열린·재현가능·포맷네이티브 한국어 Easy-Read 엔진."* "한국어 Easy-Read AI 최초"는 주장 금지(온글/KCI/KIPS 선행 — 반증 가능, 검증 게이트에서 신뢰 손상).

### 10.3 인큐번트별 포지셔닝 (NIPA/과기정통부 심사 대응)
- **vs 온글**(가장 위험한 referee 반론 — 심사위원이 안다): 개발계획서에서 *명시적으로 선제 대응*. 또박 = 온글 폐쇄 B2B SaaS의 **열린·감사가능·개발자 대면** 카운터파트. 온글 = 유료 SaaS, API/점수 불투명, 사람감수 게이트; 또박 = Apache-2.0 자가호스팅·MCP 임베드·감사 가능 + 투명 규칙별 점수 + 자동 Fidelity 게이트로 사람 감수가 닿을 수 없는 >99% 문서로 확장(소소한소통 자체 <1% 통계). *킬러가 아니라 보완 인프라*로 — 심사위원은 겸손+생태계 사고를 보상.
- **vs KCI/KIPS 논문**: 둘 다 선행연구/동기로 *인용*(학술성+정직성, 검증 게이트). 차별: "이들은 방법론·트레이드오프를 입증; 또박은 그것을 배포·재현 가능한 설치형 엔진(자가교정 루프+포맷 수집)으로 *operationalize*." K-ER 규칙을 공개 한국 지침에 근거.
- **vs WIA 글살림**(동일 대회): *장애 축*으로 차별. "WIA는 문서를 **지각 가능(PERCEIVABLE)** 하게, 또박은 **이해 가능(UNDERSTANDABLE)** 하게." 측정 가능한 깊이(K-ER·Fidelity 롤백) vs WIA의 폭.
- **vs kordoc/hwp-mcp/GongMun-Doctor**: 위협을 *자산*으로 — 클린 파서(hwp-hwpx-parser Apache / kordoc MIT) 채택·인용. 파싱 재구축 0. "한국 OSS 재사용+기여" 서사 + 리스크 경감.
- **픽토그램**: easyread-dsl은 LLM 생성 Easy-Read 픽토그램을 하지만 체크포인트가 CC BY-NC-SA(ARASAAC 학습) → 회피. CC BY-SA Mulberry/OpenMoji 고수 + 라이선스 클린성 문서화(검증 게이트 점수 자산).

**심사 강조 순서**: (i) 측정 가능성(투명 표준근거 K-ER) → (ii) 자동 Fidelity 롤백(이 공간 유일의 완전자동 의미보존 가드) → (iii) Apache-2.0 3표면 재사용성 → (iv) <1% 격차 대비 한국 인지접근 사회 임팩트. 경쟁 공간임을 정직히(온글 명명) — 우리 엣지는 열림+측정+자가교정+포맷네이티브, 선발주자 아님.

---

## 11. 데모(3분) 스토리보드 & 평가·심사 정합

### 11.1 일정 정합 (라이브 검증 — 브리프 보정)
- 참가신청·개발계획서 6/15→**7/17**. 출품(결과보고서+소스+3분 시연영상) **8/27**(하드 월). 1차 서면평가 ~9/3, 결선 ~50팀. 멘토링 9/18~10/9. **라이선스·기능 검증 10/12~10/28**. 2차 발표평가 **11/4**. 시상식 ~12/5. (출처: NIPA 2026 사업공고 + 과기정통부 2026-06-15 보도. 일부 캐시 페이지의 10/15~10/29 2차일정은 전년도값으로 보이며 등록 후 공식 oss.kr로 재확인.) **라이선스·보안 검증은 결선 후 수상자에 적용** — 클린 라이선스가 결선→수상 전환의 필요조건.
- → 모든 것을 **킬러 3분 영상 + 클린·실행가능·잘 라이선스된 8/27 레포**에 최적화.

### 11.2 3분 영상 스토리보드 (2–3 큐레이션 문서)
1. **0:00–0:25 문제**: 어려운 고지서 실예 + 법 제10조 + <1% 격차 통계. "지각 가능 vs 이해 가능".
2. **0:25–1:00 변환 시연**: 고지서 PDF 투입 → 파싱 IR → GENERATE→MEASURE→REVISE 루프 시각화. K-ER 42→81, 위반 목록 감소 애니메이션.
3. **1:00–1:50 머니샷(Fidelity)**: LLM이 "1,295,400원→약 130만 원" 반올림한 순간 게이트가 빨강 플래그→롤백→정확 금액·납부기한 보존. 부정 플립(제외→포함) 케이스도 검수 필요 배너.
4. **1:50–2:25 산출물**: 원문/쉬운본 나란히 + 픽토그램 + 면책. 점수·Fidelity 배지.
5. **2:25–2:50 재사용성**: `pip install ttobak` + 웹 데모(MVP 보장 표면). MCP 도구 호출(에이전트)은 스트레치 완성 시 포함. Apache-2.0 + NOTICE 클로즈업.
6. **2:50–3:00 정직성**: "규칙 기반 루브릭(경험적 검증 아님), 원문 우선, 온글 등 선행 존재 — 우리 엣지는 열림+측정+자가교정."

### 11.3 심사 정합
- **1차 서면(결과보고서)**: 아키텍처 다이어그램, K-ER 델타·Fidelity recall(n·한계 정직 보고), 경쟁 지형 선제 대응, 라이선스 매트릭스.
- **2차 발표**: 라이브 데모 + 게이트 ablation(rules→+NLI→+LLM-judge) + 사회 임팩트.
- **라이선스 검증 게이트**: `pip-licenses` 스캔 결과, NOTICE/THIRD_PARTY_LICENSES, `/assets` 분리, AGPL/NC 부재 증빙, 데이터 프로비넌스 로그.

---

## 12. 2개월 마일스톤 + MVP + 스트레치

> **타당성 평결(정직)**: 전체 브리프(견고한 HWP/OCR·*검증된* K-ER·저오탐 Fidelity·신뢰 코퍼스 + 3표면)는 8주 1인에 *완주 불가*. 승리법 = 범위 강하게 축소, 해피패스 데모 엔지니어링, 과장 대신 정직(면책·한계·"규칙기반 미검증")을 큰 소리로. AI 보조는 글루코드·규칙 스캐폴딩을 ~2–4× 가속하나 코퍼스 큐레이션·라벨링·임계 보정·영상 녹화·라이선스 위생은 가속 안 함 — 후반 1/3에 배정.

### 12.1 8 스프린트 (각 ~1주, 척추 먼저 프론트로드)
- **W1(~7/7)**: 레포 + Apache-2.0 + 분리 CC BY-SA `/assets` + NOTICE/THIRD_PARTY_LICENSES. IR 정의. 실 한국 공문 8–12개 수집. LLM-agnostic provider 인터페이스(Claude/GPT API + Ollama+Kanana-1.5-8B). **산출 = 7/17 전 등록·개발계획서 제출.**
- **W2**: 파서 MVP — 텍스트+PDF(pypdf/pdfminer)→IR 우선; HWPX best-effort; OCR stub. 12문서 클린 IR.
- **W3**: GENERATE→MEASURE→REVISE 루프 end-to-end(텍스트 입력). K-ER 투명 규칙 루브릭→0–100 + 위반. 경험적 검증 미주장.
- **W4(스타)**: Fidelity 게이트. 슬롯 추출·대조·롤백. 30–50 케이스 수작업 라벨 테스트셋(주입 왜곡=양성, 충실=음성). 왜곡 고recall 튜닝, fail-safe='검수 필요'.
- **W5**: 렌더러(나란히 HTML + 면책 + K-ER + Fidelity 배지). 픽토그램 = ~150–300 개념 수작업 사전 룩업(일반 시맨틱 아님). 선택 TTS(Web Speech API).
- **W6**: 두 번째 표면 1개. **권장 = MCP 서버**(클린 코어 위 저비용, 재사용 OSS/에이전트 서사, 주제 정합). 웹 데모는 동일 렌더러를 Gradio/FastAPI로 — 거의 무비용 추가 표면.
- **W7**: 12문서 해피패스 하드닝. README/docs, 아키텍처 다이어그램, 평가 수치(K-ER 델타, Fidelity recall — n·한계 정직). 기능 동결.
- **W8(~8/27)**: 3분 영상(end-to-end 성공 2–3 큐레이션 문서, 고지서 Fidelity 머니샷). 최종 라이선스 감사, 보안 패스(시크릿/dep-license 스캔), 릴리스 태그.

### 12.2 MVP 정의 (8/27까지 반드시 존재 — 없으면 컷)
1. **입력**: 텍스트+PDF+HWPX(best-effort)→IR. (이미지 OCR = 스트레치)
2. **파이프라인**: 에이전트 GENERATE→MEASURE→REVISE, provider-agnostic, 데모 기본 API 모델 + Kanana-1.5-8B(Apache) 로컬 폴백 문서화.
3. **K-ER**: 투명 규칙 루브릭→0–100 + 위반 목록. "규칙 기반·미검증" 정직 프레이밍.
4. **Fidelity 게이트(헤드라인 AI)**: 숫자/날짜/금액/기한/자격/엔티티 추출·검증·롤백; 고recall fail-safe. 30–50 케이스 라벨셋 recall 보고.
5. **렌더러**: 나란히 HTML + 상시 면책 + K-ER·Fidelity 배지. ~150–300 개념 픽토그램 룩업.
6. **표면**: 파이썬 패키지 + {웹(동일 렌더러 Gradio/FastAPI), MCP 서버} 중 1개. 둘 다 코어 얇은 래퍼 → 2–3표면 주장 가능하나 비코어 1개만 MVP 필수.
7. **평가**: 8–12 실문서 end-to-end, before/after K-ER 델타 + Fidelity recall(n·한계).
8. **라이선스 위생**: Apache-2.0 코드, 분리 CC BY-SA `/assets`, NOTICE/THIRD_PARTY_LICENSES, AGPL(pyhwp)·NC(ARASAAC/KAAC/EXAONE/Kanana-2-30B) 부재.
9. **3분 영상**(Fidelity 머니샷 포함).

### 12.3 스트레치 (뒤에서부터 컷)
이미지 OCR → 시맨틱/임베딩 픽토그램 매칭 → TTS → 두 번째 비코어 표면 → 로컬 모델 API 동등성 → K-ER 경험적 검증 시도 → 멀티문서/배치 → 광범위 HWP(.hwp 바이너리) 견고성.

### 12.4 워스트케이스 플로어
거의 다 미끄러져도: 붙여넣은 한국어 텍스트 → 규칙 기반 K-ER 점수 + 숫자/기한 왜곡을 잡는 Fidelity 게이트 → 나란히 + 면책, 3 실문서 시연, 클린 Apache-2.0 레포의 CLI/파이썬 도구. 이것만으로 일관·정직·주제정합·라이선스클린 출품으로 결선 도달 가능. 파싱 폭·OCR·픽토그램·추가 표면은 그 위 업사이드.

---

## 13. 리스크 레지스터

| # | 리스크 | 심각도 | 완화 | 컷 옵션 |
|---|---|---|---|---|
| R1 | **K-ER 지표 타당성/보정** — 공개·검증 한국 Easy-Read 라벨 코퍼스 부재(질적 지침·학년 공식만 존재). 8/27까지 경험적 검증 불가. 과장은 기술 심사 신뢰 타격, 검증 추구는 다주 시간 싱크. | HIGH | 투명 규칙 루브릭으로 재프레이밍(공개 한국 지침 인용), 문서·영상에서 "규칙기반·미검증" 명시. 5–10문서 face validity 스팟체크(예시적, 통계 아님). | 단일 0–100 숫자 제거, 규칙별 위반 체크리스트(pass/fail)만 — 정직·유용·공격 불가. |
| R2 | **견고한 HWP/HWPX + 이미지 OCR 파싱** — Apache/순수파이썬이 추출 *품질* 보장 안 함(legacy .hwp, 복잡 표, 다단, 스캔). 잘못된 파서가 전 파이프라인·데모 오염. | HIGH | 입력 티어링: 텍스트+PDF PRIMARY/신뢰, HWPX best-effort, 미지원은 우아한 저하. 깨끗이 파싱되는 데모 문서 큐레이션. 파싱은 수단, 헤드라인 아님. | 이미지 OCR 전부 스트레치; legacy .hwp 바이너리 컷(HWPX-only). HWPX도 불안정 시 PDF/텍스트만 데모, HWP는 로드맵. |
| R3 | **Fidelity 게이트 신뢰성**(숫자/자격 왜곡 검출, 저오탐) — 헤드라인 AI이자 최난 정합성 문제. 너무 느슨=의미드리프트 ship(파국), 너무 엄격=정당 단순화 오탐. 라벨 없이 균형 난해. | HIGH | 고가치 닫힌 필드 집합(숫자/날짜/금액/기한/자격/엔티티) regex+정규화 대조. 왜곡 고recall, fail-safe='검수 필요'. 30–50 케이스 수작업 셋 recall 정직 보고. | 숫자+날짜+금액+기한만(자격/엔티티 시맨틱=가장 퍼지, 스트레치). 신뢰 수치 가드만으로도 설득·시연 가능. |
| R4 | **3표면 전부 배포** — 1인 과욕. 각 패키징·오류처리·docs·데모 부담, 후반 코퍼스/보정/영상 시간과 경쟁. | MEDIUM | 클린 파이썬 코어 먼저, 웹/MCP는 얇은 래퍼. 웹=동일 렌더러 Gradio/FastAPI. 한 코드베이스로 2–3표면 제시. | MVP = 파이썬 패키지 + 비코어 1개(권장 MCP). 웹은 nice-to-have; 시간 부족 시 라이브 웹 대신 스크린샷/영상 + MCP ship. |
| R5 | **픽토그램 매칭 품질(+SA 구조)** — 클린 티어에 한국 네이티브 세트 없음(ARASAAC/KAAC NC). Mulberry 미유지 플래그, OpenMoji CC BY-SA 4.0. 일반 시맨틱 매칭은 데모에서 우스꽝스럽기 쉬움. SA가 Apache 코드 전염 안 하게 구조화 필요. | MEDIUM | 시맨틱 대신 ~150–300 고빈도 개념 수작업 사전. `/assets` 분리 CC BY-SA + 출처표시 + 변경기록; 코드 Apache 유지. 항상 한국어 캡션 병기. | 픽토그램 스트레치(텍스트 전용 MVP), 또는 ~30개 확신 개념(날짜/돈/전화/신청/마감)만. Easy-Read 가치는 픽토그램 없이도 성립. |
| R6 | **신뢰 평가 코퍼스** — 심사는 완성도·증거 보상하나, 한국 hard/easy 페어 벤치마크 부재 + 실문서 PII/저작권. 수집은 수작업·느림. | MEDIUM | W1부터 공개 한국 안내문/고지서 8–12개 수작업(템플릿·샘플, PII 제거). before/after K-ER 델타 + Fidelity recall(n·한계). 작은 n 정직이 침묵보다 낫다. | 실문서 수집 정체 시 합성-사실적 고지서/안내문 직접 저작(합성 라벨). 실측 n=5 > 약속 n=100. |
| R7 | **라이선스/보안 검증 게이트 + 의존성 드리프트** — 별도 라이선스·보안 검증(수상자). 단일 AGPL(pyhwp)/NC(ARASAAC/EXAONE/Kanana-2-30B) 또는 코드 라이선스 오염 자산이 수상 무산. 전이 의존·LLM 제안 NC 모델로 사고 발생 쉬움. | MEDIUM | W1부터 Apache-2.0 LICENSE, NOTICE+THIRD_PARTY_LICENSES, 분리 `/assets`. 출품 전 `pip-licenses` 스캔. Qwen2.5는 7B/14B/32B(Apache), Kanana-1.5-8B/2.1B(Apache), EXAONE/Kanana-2 shipped 경로 제외(선택 문서). 시크릿/PII 부재. | 클린 컴포넌트 불가 시 API 전용 LLM(Claude/GPT) 데모 + 로컬 경로 선택 문서화 — 로컬 모델 라이선스 노출 제거. NC 자산 건드리기 전에 픽토그램부터 컷. |

---

## 14. 테스트 전략

### 14.1 단위 테스트 (결정론 핵심 = recall 1.0 목표)
- **정규화기 스위트**: 한글 수치(`'삼만원'→30000`, `'약 3억 원'→300000000`, `'3만5천원'→35000`), 날짜(`'2026년 7월 17일까지'→ISO+inclusive`, 상대 D-7 with RELATIVE_BASE), 전화/금액. 이중 라이브러리(korean-number vs es-hangul) 교차검증, 불일치 시 실패.
- **경계어 테이블**: 이상/초과/이하/미만/까지/부터 정확 매핑 — 생성기가 약화 못 하게.
- **IR 파서**: 12문서 골든 IR 스냅샷, 블록 타입·신뢰도 검증.

### 14.2 Fidelity 게이트 평가 (6.9절 = 핵심 대회 증거)
- 주입형 왜곡 벤치마크: 타입별 recall, 타입 국소화 혼동행렬, distorted-vs-clean P/R/F1, clean control FP율, 컴포넌트 ablation, **PASS 출력 잔존 왜곡율(~0 목표)**. NLI 임계는 held-out dev 분할로 보정(과신 방어 collective confidence).

### 14.3 K-ER 평가
- 규칙별 단위 테스트(각 규칙이 알려진 위반/비위반 문장에서 정확 발화). 50–150 앵커 페어로 LLM-judge 신뢰도 임계 보정. **경험적 타당성 미주장** — face validity 스팟체크만 라벨.

### 14.4 통합 / end-to-end
- 8–12 실문서 파이프라인 통과(파싱→루프→K-ER→Fidelity→렌더). before/after K-ER 델타 보고. REVISE 자동해결율(N 내) + HUMAN_REVIEW 큐 로그(실세계 precision 체크).
- LLM provider 모킹(결정론 CI) + 라이브 스모크(녹화).

### 14.5 라이선스/보안 CI
- `pip-licenses` 게이트(허용 라이선스 allowlist; AGPL/GPL/NC 발견 시 빌드 실패). 시크릿 스캔. `/assets` 분리 검증. 법적 조건 fidelity 샘플은 korean-law MCP로 권위 텍스트 교차확인(소스가 법령 인용 시).

### 14.6 접근성 / 렌더러
- 렌더 HTML 레이아웃 규칙 자동 점검(폰트≥14pt, 좌측정렬, 면책 상시 존재, 대비). 키보드 내비·스크린리더 스모크.

---

## 15. 미해결 / 결정 필요 항목 (결정 + 가정 명시)

브리프 규칙상 TODO/TBD 금지 — 각 항목에 *내린 결정*과 *근거 가정*을 명시한다.

1. **K-ER 단일 0–100 점수 vs 체크리스트 (블로커성 우려, R1)** — **결정: MVP는 0–100 점수와 규칙별 위반 목록을 함께 산출하되, "규칙 기반 루브릭, 경험적 미검증"을 모든 표면에 명시.** 점수가 발표에서 방어 불가로 드러나면 즉시 체크리스트(pass/fail) 우선으로 격하. *가정*: 심사위원은 과장된 정밀 점수보다 투명·감사가능 위반 목록을 더 신뢰한다(레드팀·타당성 일치).

2. **2차 발표평가 날짜** — **결정: NIPA 2026 공고 기준 2차 발표평가 11/4로 둔다(출처: NIPA 사업공고·과기정통부 2026-06-15 보도). 8/27 하드 월에 최적화하고 발표 일정은 등록 직후 공식 oss.kr로 재확인.** *가정*: 일부 캐시 페이지의 10/15~10/29는 전년도값; 어느 쪽이든 8/27 출품물 품질이 결정적이라 영향 없음.

3. **로컬 한국어 LLM 기본값** — **결정: 데모 기본 = API 모델(Claude/GPT, 품질). 로컬 = Kanana-1.5-8B(Apache-2.0, 한국어 강함)를 1순위 폴백, Qwen2.5-7B/14B(Apache)를 2순위로 문서화.** EXAONE/Kanana-2-30B는 shipped 경로 제외(NC/게이트). *가정*: 데모 품질과 OSS 순수성을 동시에 — API로 시연, 로컬 클린 경로 문서화.

4. **HWP/HWPX 추출 품질 미지(R2)** — **결정: hwp-hwpx-parser를 핀하되 텍스트/PDF를 PRIMARY로, HWPX는 best-effort.** legacy .hwp 바이너리는 로드맵. *가정*: 12개 데모 문서를 깨끗이 파싱되는 것으로 큐레이션하면 파이프라인 가치(Easy-Read+Fidelity)를 텍스트/PDF만으로도 증명. 폴백으로 kordoc(MIT, Node)를 서브프로세스 경계로 두는 옵션 문서화.

5. **픽토그램 한국 네이티브 세트 부재(R5)** — **결정: Western 세트(Mulberry/OpenMoji) + 한국어 캡션으로 진행, 수작업 ~150–300 개념 사전.** *가정*: 클린 티어에 한국 네이티브 세트가 없으므로(ARASAAC/KAAC NC) 캡션 병기로 문화 격차 완화. 시간 부족 시 ~30 핵심 개념으로 축소 또는 픽토그램 스트레치화.

6. **Fidelity 시맨틱 범위(R3)** — **결정: MVP는 숫자/날짜/금액/기한을 정확일치로(무관용), 자격/조건/부정은 NLI+NegationGuard로 best-effort.** 시간 부족 시 자격/엔티티 시맨틱을 스트레치로 격하하고 정량 가드만 유지. *가정*: 정량 가드만으로도 설득력 있는 사회적 결과 + 시연 가능.

7. **코퍼스 실문서 수집 가능성(R6)** — **결정: KOGL-1 + data.go.kr(CC BY) 실문서를 우선 수집하되, 정체 시 합성-사실적 문서로 폴백(명시 라벨).** AI Hub·모두의 말뭉치는 `/dev-only/`(gitignored) 사적 평가 전용. *가정*: 재배포 가능성이 수집 편의보다 우선 — 공개 코퍼스는 100% 재배포 가능 자료로만.

8. **MCP SDK 버전** — **결정: `mcp>=1.27,<2` 핀(상류 README 권장).** *가정*: v2 stable 목표 ~2026-07-27, alpha는 이미 배포 중 — 안정 v1.x가 출품(8/27)까지 충분하며 alpha 파손 회피가 우선.

9. **두 번째 표면 선택(R4)** — **결정: 비코어 표면은 MCP 서버를 우선(클린 코어 위 저비용 + 에이전트/재사용 OSS 서사 + 주제 정합), 웹 데모는 동일 렌더러 래퍼로 무비용 추가.** *가정*: 1인 8주에 3 완성 표면은 과욕이므로 코어+1 필수, 나머지는 얇은 래퍼.

---

*문서 끝. 본 명세의 모든 라이선스·문헌·경쟁·코퍼스 사실은 2026-06-30 라이브 웹 검증 결과이며 출처 URL을 각 절에 명시했다. 구현 중 사실이 변하면(특히 라이브러리 버전·라이선스·대회 일정) 재검증한다.*
