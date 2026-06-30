import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from ttobak.eval.corpus import CorpusPair, FidelityChecks, SourceLicense, load_corpus, validate_corpus

VALID_ROW = {
    "pair_id": "kogl1-0001",
    "source_text": "건강보험료 1,295,400원을 2026년 7월 17일까지 납부하십시오.",
    "easy_text": "건강보험료 1,295,400원을 2026년 7월 17일까지 내세요.",
    "source_license": {"type": "KOGL-1", "attribution": "국민건강보험공단, 2026, 건강보험료 안내문",
                       "url": "https://www.nhis.or.kr/example", "date_fetched": "2026-06-30"},
    "ker_score": 78.5,
    "ker_rule_violations": ["long_sentence", "sino_korean_word"],
    "fidelity_checks": {"numbers": True, "dates": True, "amounts": True, "deadlines": True,
                        "eligibility": True, "entities": True, "distortions": []},
    "pictogram_refs": [{"set": "openmoji", "glyph_id": "1F4B0", "modified": False}],
    "reviewer": "solo-reviewer", "review_date": "2026-07-05",
}


def test_corpus_pair_parses_valid_row():
    pair = CorpusPair(**VALID_ROW)
    assert pair.pair_id == "kogl1-0001"
    assert isinstance(pair.source_license, SourceLicense)
    assert isinstance(pair.fidelity_checks, FidelityChecks)
    assert pair.source_license.type == "KOGL-1"
    assert pair.fidelity_checks.deadlines is True


def test_corpus_pair_rejects_missing_license():
    bad = dict(VALID_ROW); del bad["source_license"]
    with pytest.raises(ValidationError):
        CorpusPair(**bad)


def test_load_corpus_reads_jsonl(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    rows = [VALID_ROW, {**VALID_ROW, "pair_id": "kogl1-0002"}]
    p.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows), encoding="utf-8")
    pairs = load_corpus(p)
    assert [x.pair_id for x in pairs] == ["kogl1-0001", "kogl1-0002"]


def test_load_corpus_skips_blank_lines(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    p.write_text(json.dumps(VALID_ROW, ensure_ascii=False) + "\n\n   \n", encoding="utf-8")
    assert len(load_corpus(p)) == 1


def test_validate_corpus_raises_on_bad_row(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    bad = dict(VALID_ROW); del bad["ker_score"]
    p.write_text(json.dumps(bad, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValidationError):
        validate_corpus(p)


def test_validate_corpus_returns_pairs_on_good_file(tmp_path: Path):
    p = tmp_path / "pairs.jsonl"
    p.write_text(json.dumps(VALID_ROW, ensure_ascii=False), encoding="utf-8")
    assert validate_corpus(p)[0].pair_id == "kogl1-0001"
