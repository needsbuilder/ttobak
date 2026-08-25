"""또박(Ttobak) 코퍼스 주석기 — (source, easy) 페어를 실제 엔진으로 채점해 주석을 산출한다.

코퍼스 주석(ker_score·규칙 위반·필드별 fidelity·픽토그램)은 손으로 지어내지 않고
이 스크립트로 **실제 코드를 실행**해 도출한다(재현 가능성 = 정직성). gold 페어는
fidelity 게이트에서 ``verdict == PASS`` 여야 한다(사실 보존 확인).

사용:
    python -m tooling.annotate_corpus "<source_text>" "<easy_text>"        # 단일 페어 채점(JSON)
    python -m tooling.annotate_corpus --seed                                # corpus/pairs.jsonl 첫 줄 재채점
    python -m tooling.annotate_corpus --corpus                              # corpus/pairs.jsonl 전체 재채점 + 집계

프로그램적으로:
    from tooling.annotate_corpus import annotate
    ann = annotate(source_text, easy_text, ref=date(2026, 7, 1))
"""
from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

from ttobak.parse import parse
from ttobak.metric import score
from ttobak.fidelity import verify
from ttobak.pictogram import match
from ttobak.levels import Level

REF_DATE = date(2026, 7, 1)

# fidelity 슬롯 타입 → 코퍼스 fidelity_checks 카테고리
_SLOT_TO_CATEGORY = {
    "money": "amounts",
    "numeric": "numbers",
    "date": "dates",
    "deadline": "deadlines",
    "scope": "eligibility",
    "contact": "entities",
    "agency": "entities",
    "person": "entities",
    "negation": "eligibility",
}
_CATEGORIES = ["numbers", "dates", "amounts", "deadlines", "eligibility", "entities"]


def _verdict_str(v) -> str:
    return str(getattr(v, "value", v))


def annotate(source_text: str, easy_text: str, ref: date = REF_DATE) -> dict:
    """실제 엔진으로 페어를 채점해 코퍼스 주석 dict를 반환한다."""
    doc = parse(source_text, "text/plain")
    before = score(source_text, Level.EASY, None)
    after = score(easy_text, Level.EASY, source_text)
    fid = verify(doc, easy_text, ref)
    pics = match(easy_text)

    verdict = _verdict_str(fid.verdict).upper()  # Verdict enum value is lowercase ("pass")
    passed = verdict == "PASS"

    # 각 카테고리는 해당 타입 슬롯이 하나라도 실패하면 False. PASS면 전부 보존.
    failed_types = {_verdict_str(s.type) for s in fid.failed_slots}
    checks: dict[str, object] = {}
    for cat in _CATEGORIES:
        cat_failed = any(_SLOT_TO_CATEGORY.get(ft) == cat for ft in failed_types)
        checks[cat] = passed or not cat_failed
    distortions: list[str] = []
    if not passed:
        distortions = sorted({_SLOT_TO_CATEGORY.get(ft, ft) for ft in failed_types})
        for flag in getattr(fid, "drift_flags", []) or []:
            distortions.append(str(flag))
    checks["distortions"] = distortions

    return {
        "ker_score": round(after.score, 1),
        "ker_level_estimate": after.level_estimate,
        "ker_rule_violations": [f"{v.rule}:{v.span}" for v in after.violations],
        "fidelity_checks": checks,
        "fidelity_verdict": verdict,
        "pictogram_refs": [p.model_dump() for p in pics],
        # 진단용(코퍼스 행에는 미수록)
        "_before_score": round(before.score, 1),
        "_before_violation_count": len(before.violations),
        "_delta": round(after.score - before.score, 1),
        "_exact_fail_count": fid.exact_fail_count,
        "_drift_flags": list(getattr(fid, "drift_flags", []) or []),
        "_slot_types": sorted({_verdict_str(s.type) for s in fid.slots}),
    }


def summarize_corpus(path: Path | str = "corpus/pairs.jsonl") -> dict:
    """코퍼스 전체를 현재 엔진으로 재채점해 페어별 값과 집계를 낸다.

    README·결과보고서·DATASET_CARD 가 인용하는 집계 수치(n, 평균 K-ER, Δ, 위반 평균)의
    유일한 출처다. 손으로 적지 않는다 — 이 함수를 돌려 나온 값을 옮긴다.
    """
    rows = [
        json.loads(line)
        for line in Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    pairs = []
    for row in rows:
        ann = annotate(row["source_text"], row["easy_text"])
        pairs.append(
            {
                "pair_id": row.get("pair_id"),
                "before": ann["_before_score"],
                "after": ann["ker_score"],
                "delta": ann["_delta"],
                "recorded": row.get("ker_score"),
                "violations_before": ann["_before_violation_count"],
                "violations_after": len(ann["ker_rule_violations"]),
                "fidelity_verdict": ann["fidelity_verdict"],
            }
        )

    def _mean(key: str) -> float:
        return round(sum(p[key] for p in pairs) / len(pairs), 2) if pairs else 0.0

    before_mean, after_mean = _mean("before"), _mean("after")
    vb_mean, va_mean = _mean("violations_before"), _mean("violations_after")
    return {
        "n": len(pairs),
        "before_mean": before_mean,
        "after_mean": after_mean,
        "delta": round(after_mean - before_mean, 2),
        "violations_before_mean": vb_mean,
        "violations_after_mean": va_mean,
        "violations_delta": round(va_mean - vb_mean, 2),
        "all_fidelity_pass": all(p["fidelity_verdict"] == "PASS" for p in pairs),
        "delta_range": [min(p["delta"] for p in pairs), max(p["delta"] for p in pairs)] if pairs else [],
        "pairs": pairs,
    }


def _main(argv: list[str]) -> int:
    if "--corpus" in argv:
        summary = summarize_corpus()
        print(json.dumps(summary, ensure_ascii=False, indent=2))
        return 0
    if "--seed" in argv:
        first = Path("corpus/pairs.jsonl").read_text(encoding="utf-8").splitlines()[0]
        row = json.loads(first)
        ann = annotate(row["source_text"], row["easy_text"])
        ann["_recorded_ker_score"] = row.get("ker_score")
        print(json.dumps(ann, ensure_ascii=False, indent=2))
        return 0
    args = [a for a in argv if not a.startswith("--")]
    if len(args) != 2:
        print(__doc__)
        return 2
    print(json.dumps(annotate(args[0], args[1]), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
