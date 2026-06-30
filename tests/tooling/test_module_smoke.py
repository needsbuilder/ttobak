from pathlib import Path

from tooling.check_licenses import check_assets_separation, check_no_secrets, run_audit

ROOT = Path(__file__).resolve().parents[2]


def test_real_tree_has_no_asset_leak_or_secrets():
    # Filesystem gates only (no live pip-licenses): the committed tree must be clean.
    violations = []
    violations.extend(check_assets_separation(ROOT))
    violations.extend(check_no_secrets(ROOT))
    assert violations == [], [(v.kind, v.detail) for v in violations]


def test_run_audit_with_empty_packages_skips_license_check():
    # packages=[] -> license classifier finds nothing; only filesystem gates run.
    violations = run_audit(ROOT, packages=[])
    assert violations == [], [(v.kind, v.detail) for v in violations]
