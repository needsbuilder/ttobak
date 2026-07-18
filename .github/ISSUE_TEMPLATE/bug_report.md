---
name: 버그 신고 (Bug report)
about: 잘못 동작하는 부분을 알려 주세요
labels: bug
---

## 무엇이 잘못되었나요?

<!-- 실제로 일어난 일을 적어 주세요 -->

## 재현 방법

```python
# 재현 가능한 최소 코드 또는 명령
```

## 기대한 동작

## 환경

- OS:
- Python 버전:
- 설치 방법: (`pip install -e ".[dev]"` / 기타)
- provider: (fake / anthropic / ollama)

## Fidelity 게이트 관련이라면

- 원문(source_text)과 쉬운본(easy_text) 예시를 함께 붙여 주세요.
- 왜곡이 통과(PASS)됐다면 특히 중요한 신고입니다 — `verify()` 결과의
  `verdict`·`failed_slots`·`drift_flags`를 같이 적어 주세요.
