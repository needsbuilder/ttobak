from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_ci_workflow_exists_and_runs_the_three_gates():
    wf = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")
    # triggers
    assert "push" in wf
    assert "pull_request" in wf
    # gate 1: tests
    assert "pytest" in wf
    # gate 2: license allowlist
    assert "scripts/check_licenses.py" in wf
    # gate 3: assets separation
    assert "check_assets_separation" in wf
    # installs the dev extra so pip-licenses/pytest are present
    assert ".[dev]" in wf


def test_readme_states_honesty_framing_and_mvp():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "Apache-2.0" in readme
    # spec §5.3 / §3.1 honesty framing must be visible
    assert "원문이 우선" in readme or "원문 우선" in readme
    assert "규칙 기반" in readme
