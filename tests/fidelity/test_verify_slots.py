from datetime import date

from ttobak.fidelity.models import Slot, SlotType
from ttobak.fidelity.verify_slots import verify_high_slots

REF = date(2026, 7, 10)


def _money(raw, value):
    return Slot(raw_span=raw, normalized_value=value, type=SlotType.MONEY)


def _date(raw, value):
    return Slot(raw_span=raw, normalized_value=value, type=SlotType.DATE)


def test_number_swap_caught():
    failed = verify_high_slots([_money("30,000원", "30000")], "보험료는 3,000원입니다.", REF)
    assert len(failed) == 1
    assert failed[0].normalized_value == "30000"


def test_clean_money_passes():
    assert verify_high_slots([_money("1,295,400원", "1295400")], "이번 달에 내야 할 돈은 1,295,400원입니다.", REF) == []


def test_korean_number_in_easy_text_survives():
    assert verify_high_slots([_money("30,000원", "30000")], "보험료는 삼만원입니다.", REF) == []


def test_date_drift_caught():
    failed = verify_high_slots([_date("2026년 7월 17일", "2026-07-17")], "신청은 2026년 7월 7일까지입니다.", REF)
    assert len(failed) == 1


def test_rounding_without_allowlist_fails():
    failed2 = verify_high_slots([_money("1,295,400원", "1295400")], "약 130만 원 정도입니다.", REF)
    assert len(failed2) == 1  # exact 1295400 absent, no opt-in allowlist


def test_rounding_allowlist_three_conditions_pass():
    s = Slot(raw_span="약 130만 원", normalized_value="1295400", type=SlotType.MONEY)
    failed = verify_high_slots([s], "약 130만 원 정도입니다.", REF, rounding_allowlist={"1295400"})
    assert failed == []


def test_rounding_allowlist_but_no_hedge_in_easy_fails():
    s = Slot(raw_span="약 130만 원", normalized_value="1295400", type=SlotType.MONEY)
    failed = verify_high_slots([s], "130만 원입니다.", REF, rounding_allowlist={"1295400"})
    assert len(failed) == 1
