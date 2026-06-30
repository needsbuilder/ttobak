"""K-ER report models (canonical contract)."""
from __future__ import annotations

from pydantic import BaseModel

from ttobak.common import Severity


class Violation(BaseModel):
    rule: str
    span: str
    severity: Severity
    suggestion: str


class KERReport(BaseModel):
    score: float
    level_estimate: int
    sub_scores: dict[str, float]
    violations: list[Violation]
