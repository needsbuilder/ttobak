from ttobak.common import Severity, Verdict
from ttobak.fidelity.models import SlotType, Slot, FidelityReport


def test_slot_type_values_are_lowercase_name():
    assert SlotType.NUMERIC.value == "numeric"
    assert SlotType.DATE.value == "date"
    assert SlotType.MONEY.value == "money"
    assert SlotType.DURATION.value == "duration"
    assert SlotType.ELIGIBILITY.value == "eligibility"
    assert SlotType.AGENCY.value == "agency"
    assert SlotType.CONTACT.value == "contact"
    assert SlotType.PERSON.value == "person"
    assert SlotType.NEGATION.value == "negation"
    assert SlotType.CONDITIONAL.value == "conditional"
    assert SlotType.MODALITY.value == "modality"
    assert SlotType.SCOPE.value == "scope"


def test_slot_defaults():
    s = Slot(raw_span="삼만원", normalized_value="30000", type=SlotType.MONEY)
    assert s.polarity is True
    assert s.source_offset == 0
    assert s.criticality == Severity.HIGH


def test_slot_str_enum_is_str_subclass():
    assert isinstance(SlotType.MONEY, str)


def test_fidelity_report_defaults():
    s = Slot(raw_span="2026년 7월 17일", normalized_value="2026-07-17", type=SlotType.DATE)
    r = FidelityReport(slots=[s], verdict=Verdict.PASS)
    assert r.exact_fail_count == 0
    assert r.nli_contradictions == []
    assert r.drift_flags == []
    assert r.failed_slots == []
    assert r.slots[0].type == SlotType.DATE
