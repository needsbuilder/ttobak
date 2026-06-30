from scripts.check_licenses import ALLOWLIST, DENYLIST_SUBSTR, check_licenses


def test_clean_permissive_packages_pass():
    pkgs = [
        {"Name": "pypdf", "License": "BSD-3-Clause"},
        {"Name": "pdfminer.six", "License": "MIT License"},
        {"Name": "hwp-hwpx-parser", "License": "Apache-2.0"},
        {"Name": "dateparser", "License": "Apache Software License"},
    ]
    assert check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR) == []


def test_lgpl_is_allowed_separate_dep():
    # kiwipiepy is LGPL-3.0 and explicitly permitted (spec §9.1, separate dep)
    pkgs = [{"Name": "kiwipiepy", "License": "LGPL-3.0"}]
    assert check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR) == []


def test_agpl_is_flagged():
    pkgs = [{"Name": "pyhwp", "License": "GNU Affero General Public License v3"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "pyhwp" in violations[0]


def test_gpl_is_flagged():
    pkgs = [{"Name": "some-konlpy-dep", "License": "GPL-3.0"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "some-konlpy-dep" in violations[0]


def test_non_commercial_is_flagged():
    pkgs = [{"Name": "fake-nc-asset", "License": "CC BY-NC-SA 4.0"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "fake-nc-asset" in violations[0]


def test_unknown_license_is_flagged_as_review_needed():
    pkgs = [{"Name": "mystery-pkg", "License": "UNKNOWN"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "mystery-pkg" in violations[0]


def test_denylist_wins_over_allowlist_substring():
    # A string that contains an allowed-ish token but is actually a denied license
    pkgs = [{"Name": "tricky", "License": "GNU General Public License (GPL)"}]
    violations = check_licenses(pkgs, ALLOWLIST, DENYLIST_SUBSTR)
    assert len(violations) == 1
    assert "tricky" in violations[0]
