"""Aggregate result of the Easy-Read pipeline (canonical contract)."""
from __future__ import annotations

from pydantic import BaseModel, Field

from ttobak.common import Verdict
from ttobak.fidelity.models import FidelityReport
from ttobak.ir import Document
from ttobak.levels import Level
from ttobak.metric.models import KERReport
from ttobak.pictogram.models import PictogramRef


class EasyReadResult(BaseModel):
    """Everything the renderer / web surfaces need from one run."""

    source: Document
    easy_text: str
    level: Level
    ker: KERReport
    fidelity: FidelityReport
    pictograms: list[PictogramRef] = Field(default_factory=list)
    revisions: int = 0
    verdict: Verdict
