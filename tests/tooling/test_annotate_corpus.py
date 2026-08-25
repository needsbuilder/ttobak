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


def test_recorded_ker_scores_match_a_live_rescore():
    """코퍼스에 적힌 ker_score 가 지금 엔진이 내는 값과 같아야 한다.

    어긋나면 주석이 손으로 쓰였거나 규칙이 바뀐 뒤 재주석하지 않은 것이다.
    """
    summary = summarize_corpus(CORPUS)
    drifted = [p for p in summary["pairs"] if p["recorded"] != p["after"]]
    assert not drifted, f"기록값과 재채점이 다른 페어: {drifted}"


def test_every_gold_pair_passes_the_fidelity_gate():
    assert summarize_corpus(CORPUS)["all_fidelity_pass"] is True


def test_reported_delta_is_derived_not_asserted():
    summary = summarize_corpus(CORPUS)
    assert summary["delta"] == round(summary["after_mean"] - summary["before_mean"], 2)
    assert summary["violations_delta"] == round(
        summary["violations_after_mean"] - summary["violations_before_mean"], 2
    )
