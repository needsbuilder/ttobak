# 또박(Ttobak)에 기여하기

또박은 어려운 한국어 공공문서를 쉬운 글로 바꾸는 오픈소스 엔진입니다.
이슈·PR·코퍼스 제안·픽토그램 제안 모두 환영합니다. (English contributions are
welcome too — feel free to file issues/PRs in English.)

## 로컬 개발 환경

```bash
git clone https://github.com/needsbuilder/ttobak.git
cd ttobak
python3 -m venv venv && source venv/bin/activate   # Python 3.11+
python -m pip install -e ".[dev]"
python -m pytest -q          # 전체 테스트
python -m tooling.check_licenses --root .   # 라이선스·보안 감사 게이트 (= ttobak audit)
ttobak web --provider fake   # 웹 데모 (API 키 불필요)
```

## 개발 규율 — TDD

이 저장소는 **실패 테스트 먼저** 규칙으로 개발합니다:

1. 재현하는 실패 테스트를 먼저 작성한다 (red)
2. 구현한다 (green)
3. 전체 스위트 + 감사 게이트를 돌리고 커밋한다

테스트는 도메인별 디렉터리(`tests/fidelity/`, `tests/metric/`, …)로
미러링합니다. Fidelity 게이트 관련 수정은 `tests/fidelity/test_gate_adversarial.py`
의 적대적 회귀 테스트(M1~M9) 스타일로 공격 케이스를 함께 추가해 주세요.

## 커밋 컨벤션

Conventional Commits + 스코프를 사용합니다:

```
feat(fidelity): AGENCY 슬롯 추출 추가
fix(metric): 피동 비율 span 중복 제거
docs(readme): 설치 절차 갱신
ci(audit): ruff 게이트 추가
```

## 절대 규칙 — 라이선스 경계 (CI가 강제)

- **금지 의존성**: GPL / AGPL / NC(비상업). 추가하면 CI가 빌드를 깹니다.
- `assets/`(픽토그램, CC BY-SA)는 Apache-2.0 코드 트리와 **분리 유지** — 글리프를
  코드·데이터 출력에 인라인/base64로 내장하지 마세요.
- 의존성을 추가하면 `THIRD_PARTY_LICENSES.md`와 `NOTICE`를 함께 갱신해야
  합니다 (`tests/tooling/test_notice_coverage.py`가 검증).

## 정직성 원칙

- 코퍼스 주석(`corpus/pairs.jsonl`)은 손으로 짓지 않습니다 — 반드시
  `python -m tooling.annotate_corpus`로 실제 엔진을 실행해 도출합니다.
- K-ER은 규칙 기반 루브릭이며 경험적으로 검증된 지표가 아닙니다 — 이 단서를
  문서·출력에서 제거하는 변경은 받지 않습니다.
- 쉬움과 사실 보존이 충돌하면 **사실 보존이 이깁니다** (Fidelity-first).

## PR 체크리스트

- [ ] 실패 테스트 → 구현 순서로 작성했다
- [ ] `python -m pytest -q` 전체 통과
- [ ] `python -m tooling.check_licenses --root .` 통과
- [ ] 의존성 변경 시 `THIRD_PARTY_LICENSES.md`·`NOTICE` 갱신
- [ ] 커밋 메시지가 Conventional Commits 형식이다

궁금한 점은 이슈로 열어 주세요. 작은 오타 수정부터 코퍼스 페어 제안까지,
모든 기여가 문서 접근권을 넓힙니다.
