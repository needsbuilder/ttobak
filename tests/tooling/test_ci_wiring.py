from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = ROOT / ".github" / "workflows" / "ci.yml"


def test_ci_has_license_audit_job():
    assert "license-audit:" in CI.read_text(encoding="utf-8")


def test_ci_installs_audit_extra_and_runs_gate():
    text = CI.read_text(encoding="utf-8")
    assert "[audit]" in text
    assert "tooling.check_licenses" in text


def test_ci_runs_checker_unit_tests():
    assert "tests/tooling" in CI.read_text(encoding="utf-8")
