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


def test_extracts_agency_slot():
    slots = extract_slots(_doc("자세한 사항은 강서구청에 문의하세요."), REF)
    agencies = [s for s in slots if s.type == SlotType.AGENCY]
    assert any(s.normalized_value == "강서구청" for s in agencies)


def test_extracts_agency_public_corporation():
    slots = extract_slots(_doc("국민연금공단에서 매월 지급합니다."), REF)
    agencies = [s for s in slots if s.type == SlotType.AGENCY]
    assert any(s.normalized_value == "국민연금공단" for s in agencies)


def test_agency_slots_are_high_criticality():
    from ttobak.common import Severity
    slots = extract_slots(_doc("샛별구청 민원실에 제출하세요."), REF)
    agencies = [s for s in slots if s.type == SlotType.AGENCY]
    assert agencies and agencies[0].criticality == Severity.HIGH


def test_extracts_numeric_count_slots():
    slots = extract_slots(_doc("아동 1명당 지원하며, 올해는 총 300명을 선발합니다."), REF)
    nums = {s.normalized_value for s in slots if s.type == SlotType.NUMERIC}
    assert {"1명", "300명"} <= nums


def test_extracts_numeric_comma_group_and_percent():
    # 콤마 숫자는 콤마 제거 정규화, 퍼센트/%는 '%'로 단위 통일.
    slots = extract_slots(_doc("전체 3,000가구 중 32퍼센트가 대상입니다."), REF)
    nums = {s.normalized_value for s in slots if s.type == SlotType.NUMERIC}
    assert "3000가구" in nums
    assert "32%" in nums


def test_numeric_unit_gae_does_not_capture_gaewol():
    # '6개월'은 기간(DURATION, 로드맵)이지 '6개'가 아니다 — '개'가 '개월'의
    # 접두로 오매칭되면 '3개월→세 달' 같은 정당한 변환이 거짓 REVISE를 만든다.
    slots = extract_slots(_doc("신청 후 6개월 이내에 지급하며, 서류는 3개를 제출합니다."), REF)
    nums = {s.normalized_value for s in slots if s.type == SlotType.NUMERIC}
    assert "6개" not in nums
    assert "3개" in nums


def test_numeric_does_not_reextract_money_date_contact():
    # 원(MONEY)·연월일(DATE)·전화번호(CONTACT)는 각자 슬롯 타입이 담당한다 —
    # NUMERIC이 중복 추출하면 같은 사실이 두 규칙으로 이중 판정된다.
    slots = extract_slots(
        _doc("2026년 8월 25일에 100,000원을 지급합니다. 문의 02-1234-5678."), REF)
    assert not [s for s in slots if s.type == SlotType.NUMERIC]
