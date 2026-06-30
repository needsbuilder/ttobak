from datetime import date

from ttobak.ir import Block, BlockType, Document
from ttobak.fidelity.extract import extract_slots
from ttobak.fidelity.models import SlotType

REF = date(2026, 7, 10)


def _doc(text: str) -> Document:
    return Document(blocks=[Block(type=BlockType.PARAGRAPH, text=text)], source_mime="text/plain")


def test_extracts_money_slot():
    slots = extract_slots(_doc("이번 달 보험료는 1,295,400원입니다."), REF)
    money = [s for s in slots if s.type == SlotType.MONEY]
    assert any(s.normalized_value == "1295400" for s in money)


def test_extracts_date_slot_with_inclusive_boundary():
    slots = extract_slots(_doc("납부 기한은 2026년 7월 17일까지입니다."), REF)
    dates = [s for s in slots if s.type == SlotType.DATE]
    assert any(s.normalized_value == "2026-07-17|inclusive" for s in dates)


def test_extracts_scope_boundary_slot():
    slots = extract_slots(_doc("만 65세 이상 어르신이 대상입니다."), REF)
    scope = [s for s in slots if s.type == SlotType.SCOPE]
    assert any(s.normalized_value == ">=" for s in scope)


def test_extracts_contact_slot():
    slots = extract_slots(_doc("문의: 02-1234-5678 로 연락 주세요."), REF)
    contact = [s for s in slots if s.type == SlotType.CONTACT]
    assert any(s.normalized_value == "0212345678" for s in contact)


def test_extracts_negation_slot():
    slots = extract_slots(_doc("외국인은 신청 대상에서 제외됩니다."), REF)
    neg = [s for s in slots if s.type == SlotType.NEGATION]
    assert neg and neg[0].polarity is False


def test_money_slots_are_high_criticality():
    from ttobak.common import Severity
    slots = extract_slots(_doc("보험료 30,000원"), REF)
    money = [s for s in slots if s.type == SlotType.MONEY]
    assert money and money[0].criticality == Severity.HIGH
