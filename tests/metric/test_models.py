from ttobak.common import Severity
from ttobak.metric.models import Violation, KERReport


def test_violation_fields():
    v = Violation(rule="sentence_length", span="문장 전체", severity=Severity.HIGH, suggestion="문장을 둘로 나누세요.")
    assert v.rule == "sentence_length"
    assert v.span == "문장 전체"
    assert v.severity is Severity.HIGH
    assert v.suggestion == "문장을 둘로 나누세요."


def test_ker_report_fields_and_defaults():
    v = Violation(rule="passive_ratio", span="처리됩니다", severity=Severity.MED, suggestion="능동으로 바꾸세요.")
    r = KERReport(score=81.0, level_estimate=2, sub_scores={"sentence_length": 90.0, "passive_ratio": 70.0}, violations=[v])
    assert r.score == 81.0
    assert r.level_estimate == 2
    assert r.sub_scores["passive_ratio"] == 70.0
    assert r.violations[0].rule == "passive_ratio"


def test_ker_report_empty_violations_allowed():
    r = KERReport(score=100.0, level_estimate=1, sub_scores={}, violations=[])
    assert r.violations == []
    assert r.score == 100.0
