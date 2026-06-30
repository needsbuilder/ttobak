from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel


class SourceLicense(BaseModel):
    type: str
    attribution: str
    url: str
    date_fetched: str


class FidelityChecks(BaseModel):
    numbers: bool
    dates: bool
    amounts: bool
    deadlines: bool
    eligibility: bool
    entities: bool
    distortions: list[str] = []


class CorpusPair(BaseModel):
    pair_id: str
    source_text: str
    easy_text: str
    source_license: SourceLicense
    ker_score: float
    ker_rule_violations: list[str] = []
    fidelity_checks: FidelityChecks
    pictogram_refs: list[dict] = []
    reviewer: str
    review_date: str


def load_corpus(path: Path) -> list[CorpusPair]:
    """Read a pairs.jsonl file into validated CorpusPair objects (blank lines skipped)."""
    pairs: list[CorpusPair] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pairs.append(CorpusPair(**json.loads(line)))
    return pairs


def validate_corpus(path: Path) -> list[CorpusPair]:
    """Validate a pairs.jsonl file against the schema; re-raise on any bad row."""
    return load_corpus(path)
