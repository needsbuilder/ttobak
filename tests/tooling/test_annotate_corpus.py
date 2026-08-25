"""corpus 전체 재채점 모드 — 보고서·데이터셋 카드의 집계 수치가 나오는 출처.

README·결과보고서가 "누구든 같은 명령으로 재현할 수 있다"고 말하는 그 명령이다.
집계를 손으로 적지 않고 여기서 도출한다(재현 가능성 = 정직성).
"""
from pathlib import Path

from tooling.annotate_corpus import summarize_corpus

CORPUS = Path("corpus/pairs.jsonl")


def test_summarize_corpus_covers_every_pair():
    summary = summarize_corpus(CORPUS)
    assert summary["n"] == len(CORPUS.read_text(encoding="utf-8").strip().splitlines())
    assert len(summary["pairs"]) == summary["n"]


#: 형태소 분석기 빌드 차이로 허용하는 페어 단위 K-ER 오차.
#:
#: 2026-08-25 관측: kiwipiepy 0.23.2 / kiwipiepy_model 0.23.0 으로 **버전이 같아도**
#: 플랫폼 빌드가 다르면 (macOS arm64 wheel vs manylinux x86_64 wheel) 토큰화가 갈려
#: 점수가 흔들린다. synth-0011 이 macOS 82.4 / Linux 81.9 로 0.5 차이가 났다.
#: 손으로 쓴 주석이나 규칙 변경은 이보다 훨씬 크게 움직이므로, 이 폭을 허용해도
#: 테스트의 목적(주석이 실제 엔진에서 나왔는가)은 유지된다.
KER_BUILD_TOLERANCE = 1.0


def test_recorded_ker_scores_match_a_live_rescore():
    """코퍼스에 적힌 ker_score 가 지금 엔진이 내는 값과 (오차 내에서) 같아야 한다.

    크게 어긋나면 주석이 손으로 쓰였거나 규칙이 바뀐 뒤 재주석하지 않은 것이다.
    형태소 분석기 빌드 차이는 KER_BUILD_TOLERANCE 로 흡수한다.
    """
    summary = summarize_corpus(CORPUS)
    drifted = [
        p for p in summary["pairs"]
        if abs(p["recorded"] - p["after"]) > KER_BUILD_TOLERANCE
    ]
    assert not drifted, f"기록값과 재채점이 {KER_BUILD_TOLERANCE} 넘게 다른 페어: {drifted}"


def test_every_gold_pair_passes_the_fidelity_gate():
    assert summarize_corpus(CORPUS)["all_fidelity_pass"] is True


def test_reported_delta_is_derived_not_asserted():
    summary = summarize_corpus(CORPUS)
    assert summary["delta"] == round(summary["after_mean"] - summary["before_mean"], 2)
    assert summary["violations_delta"] == round(
        summary["violations_after_mean"] - summary["violations_before_mean"], 2
    )
