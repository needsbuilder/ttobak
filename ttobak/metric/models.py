"""KER (Korean Easy-Read) readability report contract (Task 21 owns the real implementation).

This is a STUB contract used during Phase-1 skeleton (Task 16–20). Task 21 will provide
the real KERReport with full rule evaluation logic. Do NOT overwrite Task 21's version.
"""
from __future__ import annotations

from pydantic import BaseModel

from ttobak.common import Severity


class Violation(BaseModel):
    """A single readability violation found by KER."""

    rule: str
    span: str
    severity: Severity
    suggestion: str


class KERReport(BaseModel):
    """Readability score and violations for a piece of text (output of KER metric)."""

    score: float
    level_estimate: int
    sub_scores: dict[str, float]
    violations: list[Violation] = []
