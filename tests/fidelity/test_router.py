from ttobak.common import Verdict
from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.router import route


def _slot(stype=SlotType.MONEY):
    return Slot(raw_span="x", normalized_value="1", type=stype)


def test_clean_passes():
    assert route([], [], [], False) == Verdict.PASS


def test_recoverable_money_failure_revises():
    assert route([_slot(SlotType.MONEY)], [], [], False) == Verdict.REVISE


def test_recoverable_date_failure_revises():
    assert route([_slot(SlotType.DATE)], [], [], False) == Verdict.REVISE


def test_negation_flip_forces_human_review():
    assert route([], ["부정 표현 '제외'이(가) 반전됨"], [], False) == Verdict.HUMAN_REVIEW


def test_nli_contradiction_forces_human_review():
    assert route([], [], ["조건 모순"], False) == Verdict.HUMAN_REVIEW


def test_low_extraction_confidence_forces_human_review():
    assert route([], [], [], True) == Verdict.HUMAN_REVIEW


def test_eligibility_slot_failure_is_human_review():
    assert route([_slot(SlotType.ELIGIBILITY)], [], [], False) == Verdict.HUMAN_REVIEW


def test_negation_flip_beats_money_failure():
    assert route([_slot(SlotType.MONEY)], ["부정 반전"], [], False) == Verdict.HUMAN_REVIEW
