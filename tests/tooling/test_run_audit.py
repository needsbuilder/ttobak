import json
from pathlib import Path

from tooling import check_licenses
from tooling.check_licenses import run_audit, main

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _clean_repo(root: Path) -> None:
    (root / "ttobak").mkdir()
    (root / "ttobak" / "__init__.py").write_text("", encoding="utf-8")
    assets = root / "assets" / "pictograms"
    (assets / "mulberry").mkdir(parents=True)
    (assets / "openmoji").mkdir(parents=True)
    (assets / "mulberry" / "LICENSE").write_text("CC BY-SA 2.0 UK", encoding="utf-8")
    (assets / "openmoji" / "LICENSE").write_text("CC BY-SA 4.0", encoding="utf-8")


def test_run_audit_clean(tmp_path):
    _clean_repo(tmp_path)
    assert run_audit(tmp_path, packages=_load("licenses_clean.json")) == []


def test_run_audit_collects_all_checker_kinds(tmp_path):
    _clean_repo(tmp_path)
    (tmp_path / "ttobak" / "leak.svg").write_text("<svg/>", encoding="utf-8")
    (tmp_path / "ttobak" / "bad.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    kinds = {v.kind for v in run_audit(tmp_path, packages=_load("licenses_planted_gpl.json"))}
    assert "forbidden-license" in kinds
    assert "asset-leak" in kinds
    assert "secret" in kinds


def test_main_returns_1_on_planted_gpl(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_planted_gpl.json"))
    rc = main(["--root", str(tmp_path)])
    assert rc == 1
    out = capsys.readouterr().out
    assert "forbidden-license" in out and "FAIL" in out


def test_main_returns_0_on_clean_tree(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_clean.json"))
    rc = main(["--root", str(tmp_path)])
    assert rc == 0
    assert "PASS" in capsys.readouterr().out
