"""Fidelity report models (canonical contract)."""
from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from ttobak.common import Severity, Verdict


class SlotType(str, Enum):
    NUMERIC = "numeric"
    DATE = "date"
    MONEY = "money"
    DURATION = "duration"
    ELIGIBILITY = "eligibility"
    AGENCY = "agency"
    CONTACT = "contact"
    PERSON = "person"
    NEGATION = "negation"
    CONDITIONAL = "conditional"
    MODALITY = "modality"
    SCOPE = "scope"


class Slot(BaseModel):
    raw_span: str
    normalized_value: str
    type: SlotType
    polarity: bool = True
    source_offset: int = 0
    criticality: Severity = Severity.HIGH


class FidelityReport(BaseModel):
    slots: list[Slot]
    verdict: Verdict
    exact_fail_count: int = 0
    nli_contradictions: list[str] = Field(default_factory=list)
    drift_flags: list[str] = Field(default_factory=list)
    failed_slots: list[Slot] = Field(default_factory=list)
