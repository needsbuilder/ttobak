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
