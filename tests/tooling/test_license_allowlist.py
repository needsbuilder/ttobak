import json
from pathlib import Path

from tooling.check_licenses import LicenseViolation, check_license_allowlist

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def test_clean_tree_has_no_violations():
    assert check_license_allowlist(_load("licenses_clean.json")) == []


def test_planted_gpl_is_flagged():
    violations = check_license_allowlist(_load("licenses_planted_gpl.json"))
    names = {v.detail.split(" ")[0] for v in violations}
    assert "konlpy" in names
    assert "pyhwp" in names
    assert all(v.kind == "forbidden-license" for v in violations)


def test_lgpl_is_allowed_separate_dependency():
    pkgs = [{"Name": "kiwipiepy", "Version": "0.18.0", "License": "GNU Lesser General Public License v3 (LGPLv3)"}]
    assert check_license_allowlist(pkgs) == []


def test_noncommercial_license_is_flagged():
    pkgs = [{"Name": "exaone", "Version": "3.5", "License": "EXAONE AI Model License (Non-Commercial)"}]
    violations = check_license_allowlist(pkgs)
    assert len(violations) == 1 and violations[0].kind == "forbidden-license"


def test_unknown_license_is_flagged_as_review():
    pkgs = [{"Name": "mystery-lib", "Version": "1.0", "License": "UNKNOWN"}]
    violations = check_license_allowlist(pkgs)
    assert len(violations) == 1 and violations[0].kind == "unrecognized-license"


def test_known_build_tools_with_unknown_license_are_resolved():
    # setuptools/pip/wheel ship without a readable License field; pip-licenses
    # reports UNKNOWN (observed on CI setuptools 79.0.1). They are MIT and must
    # not fail the gate. Empty license string is treated the same as UNKNOWN.
    pkgs = [
        {"Name": "setuptools", "Version": "79.0.1", "License": "UNKNOWN"},
        {"Name": "pip", "Version": "26.1.1", "License": "UNKNOWN"},
        {"Name": "wheel", "Version": "0.45.1", "License": ""},
    ]
    assert check_license_allowlist(pkgs) == []


def test_known_name_override_does_not_mask_real_forbidden_license():
    # The name-based resolve applies ONLY when the reported license is unknown/
    # empty. A build tool that actually *reports* a forbidden license is still
    # flagged — the override never masks a real GPL/AGPL/NC.
    pkgs = [{"Name": "setuptools", "Version": "9.9", "License": "GPLv3"}]
    violations = check_license_allowlist(pkgs)
    assert len(violations) == 1 and violations[0].kind == "forbidden-license"
