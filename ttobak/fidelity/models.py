"""Fidelity report contract (Task 23 owns the real implementation).

This is a STUB contract used during Phase-1 skeleton (Task 16–20). Task 23 will provide
the real FidelityReport with NLI-based verification and slot tracking. Do NOT overwrite Task 23's version.
"""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from ttobak.common import Severity, Verdict


class SlotType(str, Enum):
    """Named entity / slot types for information extraction."""

    MONEY = "money"
    DATE = "date"
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    QUANTITY = "quantity"
    PERCENTAGE = "percentage"


class Slot(BaseModel):
    """Extracted information slot (e.g., amount, date, name)."""

    raw_span: str
    normalized_value: str
    type: SlotType
    polarity: bool = True
    source_offset: int = 0
    criticality: Severity = Severity.HIGH


class FidelityReport(BaseModel):
    """Semantic fidelity verification result (NLI, slot tracking, drift detection)."""

    slots: list[Slot] = []
    verdict: Verdict
    exact_fail_count: int = 0
    nli_contradictions: list[str] = Field(default_factory=list)
    drift_flags: list[str] = Field(default_factory=list)
    failed_slots: list[Slot] = Field(default_factory=list)
