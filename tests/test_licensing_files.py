from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_license_is_apache_2():
    text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in text
    assert "Version 2.0" in text


def test_notice_names_project_and_apache():
    text = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "Ttobak" in text or "또박" in text
    assert "Apache License, Version 2.0" in text


def test_third_party_lists_key_deps_and_avoided_copyleft():
    text = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    # ship-path deps must be documented
    for dep in ["hwp-hwpx-parser", "pypdf", "pdfminer.six", "dateparser", "kiwipiepy"]:
        assert dep in text, dep
    # avoided blockers must be documented as avoided (spec §9.5)
    for blocker in ["pyhwp", "KoNLPy", "EXAONE", "ARASAAC"]:
        assert blocker in text, blocker
