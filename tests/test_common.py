from enum import Enum

from ttobak.common import Severity, Verdict


def test_severity_is_str_enum_with_exact_values():
    assert issubclass(Severity, str)
    assert issubclass(Severity, Enum)
    assert Severity.HIGH.value == "high"
    assert Severity.MED.value == "med"
    assert Severity.LOW.value == "low"
    assert {m.value for m in Severity} == {"high", "med", "low"}


def test_severity_member_equals_its_string_value():
    assert Severity.HIGH == "high"


def test_verdict_is_str_enum_with_exact_values():
    assert issubclass(Verdict, str)
    assert issubclass(Verdict, Enum)
    assert Verdict.PASS.value == "pass"
    assert Verdict.REVISE.value == "revise"
    assert Verdict.HUMAN_REVIEW.value == "human_review"
    assert {m.value for m in Verdict} == {"pass", "revise", "human_review"}


def test_verdict_member_equals_its_string_value():
    assert Verdict.HUMAN_REVIEW == "human_review"
