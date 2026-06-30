"""Easy-Read pipeline: GENERATE -> MEASURE -> REVISE orchestration (spec 4.2 B).

``score`` and ``verify`` are imported at module level so tests can
monkeypatch them with deterministic stubs. The revise loop only runs while the
Fidelity verdict is REVISE; HUMAN_REVIEW (e.g. a negation flip) terminates
immediately and is never auto-revised (spec 6.7, 6.8).
"""
from __future__ import annotations

from datetime import date

from ttobak.common import Verdict
from ttobak.ir import Document
from ttobak.levels import Level
from ttobak.prompts import (
    EASY_READ_SYSTEM,
    build_generate_prompt,
    build_revise_prompt,
)
from ttobak.providers.base import LLMProvider
from ttobak.result import EasyReadResult

# Module-level references for monkeypatching in tests
import ttobak.fidelity as _fidelity_module
import ttobak.metric as _metric_module

score = _metric_module.score
verify = _fidelity_module.verify


def _ref_date(doc: Document) -> date:
    raw = doc.meta.get("ref_date")
    if isinstance(raw, date):
        return raw
    if isinstance(raw, str) and raw:
        return date.fromisoformat(raw)
    return date.today()


def simplify(
    doc: Document,
    level: Level,
    provider: LLMProvider,
    max_revise: int = 3,
) -> EasyReadResult:
    """Run generate->measure->revise and return an EasyReadResult."""
    ref_date = _ref_date(doc)
    source_text = doc.text()

    prompt = build_generate_prompt(source_text, level)
    easy_text = provider.generate(prompt, system=EASY_READ_SYSTEM)

    ker = score(easy_text, level, source_text)
    fidelity = verify(doc, easy_text, ref_date)

    revisions = 0
    while fidelity.verdict is Verdict.REVISE and revisions < max_revise:
        revise_prompt = build_revise_prompt(
            source_text, level, easy_text, ker.violations, fidelity.failed_slots
        )
        easy_text = provider.generate(revise_prompt, system=EASY_READ_SYSTEM)
        revisions += 1
        ker = score(easy_text, level, source_text)
        fidelity = verify(doc, easy_text, ref_date)

    return EasyReadResult(
        source=doc,
        easy_text=easy_text,
        level=level,
        ker=ker,
        fidelity=fidelity,
        revisions=revisions,
        verdict=fidelity.verdict,
    )
