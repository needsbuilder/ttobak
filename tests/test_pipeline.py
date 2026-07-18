

import ttobak.pipeline as pipeline
from ttobak.pipeline import simplify
from ttobak.providers.fake import FakeProvider
from ttobak.ir import Document, Block, BlockType
from ttobak.levels import Level
from ttobak.common import Verdict, Severity
from ttobak.metric.models import KERReport, Violation
from ttobak.fidelity.models import FidelityReport, Slot, SlotType


def make_doc(text: str = "건강보험료 1,295,400원을 2026년 7월 17일까지 납부하여야 합니다.") -> Document:
    return Document(
        blocks=[Block(type=BlockType.PARAGRAPH, text=text)],
        source_mime="text/plain",
        meta={"ref_date": "2026-06-30"},
    )


def ker_report(score: float = 80.0, violations=None) -> KERReport:
    return KERReport(score=score, level_estimate=2, sub_scores={"rule": score}, violations=violations or [])


def fidelity_report(verdict: Verdict, failed=None) -> FidelityReport:
    return FidelityReport(
        slots=[Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY)],
        verdict=verdict,
        failed_slots=failed or [],
    )


def test_simplify_pass_on_first_try_no_revision(monkeypatch):
    monkeypatch.setattr(pipeline, "score", lambda easy_text, level, source_text=None: ker_report())
    monkeypatch.setattr(pipeline, "verify", lambda source, easy_text, ref_date: fidelity_report(Verdict.PASS))

    provider = FakeProvider(["건강보험료를 내세요.\n1,295,400원입니다.\n2026년 7월 17일까지 내세요."])
    result = simplify(make_doc(), Level.EASY, provider, max_revise=3)

    assert result.verdict is Verdict.PASS
    assert result.revisions == 0
    assert len(provider.calls) == 1
    assert result.easy_text.startswith("건강보험료를 내세요.")
    assert result.level is Level.EASY
    assert result.ker.score == 80.0


def test_simplify_revises_once_then_passes(monkeypatch):
    verdicts = iter([Verdict.REVISE, Verdict.PASS])
    failed_slot = Slot(raw_span="1,295,400원", normalized_value="1295400", type=SlotType.MONEY)

    def fake_verify(source, easy_text, ref_date):
        v = next(verdicts)
        return fidelity_report(v, failed=[failed_slot] if v is Verdict.REVISE else [])

    monkeypatch.setattr(
        pipeline, "score",
        lambda easy_text, level, source_text=None: ker_report(
            violations=[Violation(rule="hanja", span="납부", severity=Severity.MED, suggestion="'내다'로 바꾸세요.")]
        ),
    )
    monkeypatch.setattr(pipeline, "verify", fake_verify)

    provider = FakeProvider([
        "건강보험료 약 130만 원을 7월에 내세요.",
        "건강보험료 1,295,400원을 2026년 7월 17일까지 내세요.",
    ])
    result = simplify(make_doc(), Level.EASY, provider, max_revise=3)

    assert result.verdict is Verdict.PASS
    assert result.revisions == 1
    assert len(provider.calls) == 2
    revise_prompt = provider.calls[1]["prompt"]
    assert "1,295,400원" in revise_prompt
    assert "그대로" in revise_prompt
    assert result.easy_text == "건강보험료 1,295,400원을 2026년 7월 17일까지 내세요."


def test_simplify_respects_max_revise_when_never_passing(monkeypatch):
    failed_slot = Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE)
    monkeypatch.setattr(pipeline, "score", lambda easy_text, level, source_text=None: ker_report())
    monkeypatch.setattr(
        pipeline, "verify",
        lambda source, easy_text, ref_date: fidelity_report(Verdict.REVISE, failed=[failed_slot]),
    )

    provider = FakeProvider([f"시도 {i}: 7월쯤 내세요." for i in range(3)])
    result = simplify(make_doc(), Level.EASY, provider, max_revise=2)

    assert result.revisions == 2
    assert len(provider.calls) == 3            # 1 generate + 2 revise, no more
    assert result.verdict is Verdict.HUMAN_REVIEW    # residual REVISE escalated to HUMAN_REVIEW (spec 6.8 case d)


def test_simplify_human_review_no_revision(monkeypatch):
    negation_slot = Slot(
        raw_span="제외", normalized_value="제외", type=SlotType.NEGATION,
        polarity=False, criticality=Severity.HIGH,
    )
    calls = {"n": 0}

    def fake_verify(source, easy_text, ref_date):
        calls["n"] += 1
        return FidelityReport(slots=[negation_slot], verdict=Verdict.HUMAN_REVIEW,
                              nli_contradictions=["소스는 '제외'인데 출력이 '포함'으로 단언함"],
                              failed_slots=[negation_slot])

    monkeypatch.setattr(pipeline, "score", lambda easy_text, level, source_text=None: ker_report())
    monkeypatch.setattr(pipeline, "verify", fake_verify)

    provider = FakeProvider(["기초생활수급자도 포함하여 모두 신청할 수 있습니다."])
    result = simplify(make_doc("기초생활수급자는 제외하고 신청할 수 있습니다."), Level.EASY, provider, max_revise=3)

    assert result.verdict is Verdict.HUMAN_REVIEW
    assert result.revisions == 0
    assert len(provider.calls) == 1
    assert calls["n"] == 1
