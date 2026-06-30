import json
from pathlib import Path

from tooling import check_licenses
from ttobak.cli import main as cli_main

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


def test_cli_audit_clean(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_clean.json"))
    assert cli_main(["audit", "--root", str(tmp_path)]) == 0
    assert "PASS" in capsys.readouterr().out


def test_cli_audit_fails_on_gpl(tmp_path, monkeypatch, capsys):
    _clean_repo(tmp_path)
    monkeypatch.setattr(check_licenses, "collect_installed_licenses", lambda: _load("licenses_planted_gpl.json"))
    assert cli_main(["audit", "--root", str(tmp_path)]) == 1
    assert "forbidden-license" in capsys.readouterr().out
