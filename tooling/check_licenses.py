"""Ttobak license & security audit gate (spec 9.5 / 14.5).

Deterministic checks that fail the build on: GPL/AGPL/NC/proprietary code deps;
pictogram CC BY-SA assets leaking out of /assets; secrets/PII committed. The
license check operates on parsed `pip-licenses --format=json` output so it is
unit-testable with planted fixtures.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LicenseViolation:
    kind: str
    detail: str


# Permissive + separate-dependency weak-copyleft (LGPL) licenses we ship (spec 9.1, 9.4).
ALLOWED_LICENSE_SUBSTRINGS: frozenset[str] = frozenset({
    "apache", "mit", "bsd", "mpl", "mozilla public", "isc",
    "python software foundation", "psf", "the unlicense", "unlicense", "zlib",
    "lgpl", "lesser general public", "creative commons attribution 4.0",
    "cc-by-4.0", "cc by 4.0", "cc0", "public domain",
    "historical permission notice and disclaimer", "hpnd",
})

# Hard blockers: strong copyleft + non-commercial + proprietary (spec 9.5).
FORBIDDEN_LICENSE_SUBSTRINGS: frozenset[str] = frozenset({
    "agpl", "affero", "non-commercial", "noncommercial", "non commercial",
    "-nc-", " nc ", "research license", "proprietary",
})

# Normalized license values that mean "pip-licenses could not read the metadata".
_UNKNOWN_LICENSE_TOKENS: frozenset[str] = frozenset({"", "unknown", "unknown license"})

# Ubiquitous build/system packages that ship without a readable License field, so
# `pip-licenses --with-system` reports UNKNOWN (e.g. setuptools 79.0.1 on CI).
# Values are their real, verifiable licenses. Used ONLY to resolve an
# unknown/empty reported license — never to override a real one — so the gate
# stays fail-closed for genuinely unrecognized dependencies.
KNOWN_SYSTEM_LICENSES: dict[str, str] = {
    "setuptools": "MIT",
    "pip": "MIT",
    "wheel": "MIT",
}


def _normalize(text: str) -> str:
    return " ".join((text or "").lower().replace("(", " ").replace(")", " ").split())


def _is_lgpl(norm: str) -> bool:
    return "lgpl" in norm or "lesser general public" in norm


def _is_strong_gpl(norm: str) -> bool:
    if _is_lgpl(norm):
        return False
    return "gpl" in norm or "general public license" in norm


def check_license_allowlist(packages: list[dict]) -> list[LicenseViolation]:
    """Return a violation per package whose license is forbidden or unrecognized.

    Order per package: FORBIDDEN substring -> forbidden-license; strong (non-Lesser)
    GPL -> forbidden-license; ALLOWED substring -> ok; otherwise -> unrecognized-license.
    """
    violations: list[LicenseViolation] = []
    for pkg in packages:
        name = pkg.get("Name", "?")
        version = pkg.get("Version", "?")
        raw_license = pkg.get("License", "")
        norm = _normalize(raw_license)
        label = f"{name} {version} [{raw_license}]"
        # Resolve unreadable metadata for known build/system tools to their real
        # license (only when reported unknown/empty — never masks a real one).
        if norm in _UNKNOWN_LICENSE_TOKENS:
            known = KNOWN_SYSTEM_LICENSES.get((name or "").strip().lower())
            if known:
                norm = _normalize(known)
                label = f"{name} {version} [{raw_license or 'UNKNOWN'} -> {known} (known)]"
        if any(bad in norm for bad in FORBIDDEN_LICENSE_SUBSTRINGS):
            violations.append(LicenseViolation("forbidden-license", label))
            continue
        if _is_strong_gpl(norm):
            violations.append(LicenseViolation("forbidden-license", label))
            continue
        if any(ok in norm for ok in ALLOWED_LICENSE_SUBSTRINGS):
            continue
        violations.append(LicenseViolation("unrecognized-license", label))
    return violations


# --- /assets separation (spec 9.4 embed rule, 8.5 layout) -------------------

GLYPH_SUFFIXES: frozenset[str] = frozenset({".svg", ".png", ".gif", ".webp"})
CODE_DATA_DIRS: tuple[str, ...] = ("ttobak", "corpus", "tooling")
REQUIRED_PICTOGRAM_SETS: tuple[str, ...] = ("mulberry", "openmoji")
_SOURCE_SUFFIXES: frozenset[str] = frozenset({".py", ".html", ".jinja", ".j2", ".css", ".js", ".json"})
_BASE64_GLYPH_RE = re.compile(r"data:image/(?:svg\+xml|png|gif|webp);base64,")


def check_assets_separation(root: Path) -> list[LicenseViolation]:
    """Verify CC BY-SA pictogram assets stay inside /assets and never leak.

    Flags: glyph files under code/data dirs (asset-leak), base64-embedded glyphs
    in source files (asset-embed), pictogram sets missing a LICENSE (asset-missing-license).
    """
    violations: list[LicenseViolation] = []
    for top in CODE_DATA_DIRS:
        base = root / top
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file():
                continue
            suffix = path.suffix.lower()
            if suffix in GLYPH_SUFFIXES:
                violations.append(LicenseViolation("asset-leak", str(path.relative_to(root))))
                continue
            if suffix in _SOURCE_SUFFIXES:
                try:
                    text = path.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                if _BASE64_GLYPH_RE.search(text):
                    violations.append(LicenseViolation("asset-embed", str(path.relative_to(root))))

    pictogram_root = root / "assets" / "pictograms"
    if pictogram_root.exists():
        for set_name in REQUIRED_PICTOGRAM_SETS:
            set_dir = pictogram_root / set_name
            if set_dir.exists() and not (set_dir / "LICENSE").exists():
                violations.append(LicenseViolation("asset-missing-license", f"assets/pictograms/{set_name}"))
    return violations


# --- secrets / PII scan (spec 14.5, 3.2, 8.2) -------------------------------

# (label, regex). All labels except korean-rrn classify as "secret"; rrn = PII.
SECRET_PII_PATTERNS: list[tuple[str, str]] = [
    ("aws-access-key", r"AKIA[0-9A-Z]{16}"),
    ("anthropic-api-key", r"sk-ant-[A-Za-z0-9_-]{20,}"),
    ("openai-api-key", r"sk-(?:proj-)?[A-Za-z0-9]{20,}"),
    ("google-api-key", r"AIza[0-9A-Za-z_-]{35}"),
    ("slack-token", r"xox[baprs]-[0-9A-Za-z-]{10,}"),
    ("private-key", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    ("generic-secret-assign",
     r"(?i)(?:api[_-]?key|secret|password|passwd|token)\s*[:=]\s*['\"][A-Za-z0-9/+_-]{16,}['\"]"),
    ("korean-rrn", r"(?<!\d)\d{6}-[1-4]\d{6}(?!\d)"),
]

_PII_LABELS: frozenset[str] = frozenset({"korean-rrn"})

_SCAN_EXCLUDE_DIRS: frozenset[str] = frozenset({
    ".git", ".github", "__pycache__", ".pytest_cache", ".mypy_cache",
    "node_modules", "dist", "build", ".venv", "venv", "dev-only", "tests", "test",
    # .superpowers/sdd/ carries its own nested `.gitignore` (`*`) — everything
    # under it is local SDD scratch state (task briefs, review diffs) that is
    # never committed, so it can never ship. Excluding the dir avoids noise
    # from test-fixture secrets embedded in those briefs (see task-58/59/63).
    ".superpowers",
})

# CONFIRMED bypass fix: "docs" was previously a full directory exclusion,
# meaning a real secret committed anywhere under docs/ would never be
# scanned. Only pinpoint-exclude the specific known-fixture files (by exact
# relative path) rather than the whole tree.
_SCAN_EXCLUDE_FILES: frozenset[str] = frozenset({
    # Historical dev-plan doc that embeds this module's own test-fixture code
    # verbatim (AWS's publicly documented placeholder access key, a dummy
    # PEM body, a placeholder RRN) while narrating how check_no_secrets was
    # built — not real credentials. Same fixture strings as
    # .superpowers/sdd/task-58/59/63-*.md (excluded above). NOTE: don't spell
    # the placeholder key out literally in this file — the regex it's meant
    # to demonstrate would flag this comment too (self-referential match).
    "docs/superpowers/plans/2026-06-30-ttobak-mvp.md",
})

_SCANNABLE_SUFFIXES: frozenset[str] = frozenset({
    ".py", ".pyi", ".txt", ".md", ".json", ".jsonl", ".csv", ".yaml",
    ".yml", ".toml", ".cfg", ".ini", ".env", ".html", ".js", ".ts",
    ".pem", ".key", ".sh", "",
})

_COMPILED_PATTERNS = [(label, re.compile(pattern)) for label, pattern in SECRET_PII_PATTERNS]


def _should_scan(path: Path, root: Path) -> bool:
    rel = path.relative_to(root)
    if any(part in _SCAN_EXCLUDE_DIRS for part in rel.parts):
        return False
    if rel.as_posix() in _SCAN_EXCLUDE_FILES:
        return False
    return path.suffix.lower() in _SCANNABLE_SUFFIXES


def check_no_secrets(root: Path) -> list[LicenseViolation]:
    """Scan the tree for committed secrets and Korean PII (spec 14.5/3.2/8.2).

    tests/, test/, dev-only/, .superpowers/ are excluded so planted fixtures
    and private evaluation/scratch data do not trip the gate. docs/ is
    scanned like any other tree; only the specific known-fixture doc in
    _SCAN_EXCLUDE_FILES is pinpoint-excluded (see comment there).
    """
    violations: list[LicenseViolation] = []
    for path in root.rglob("*"):
        if not path.is_file() or not _should_scan(path, root):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = path.relative_to(root).as_posix()
        for label, compiled in _COMPILED_PATTERNS:
            if compiled.search(text):
                kind = "pii" if label in _PII_LABELS else "secret"
                violations.append(LicenseViolation(kind, f"{label} in {rel}"))
    return violations


# --- orchestration + entrypoint (spec 14.5) --------------------------------

def collect_installed_licenses() -> list[dict]:
    """Run pip-licenses and return its JSON. The only live-tooling call;
    tests inject packages instead. Requires the `audit` extra.

    Uses sys.executable so pip-licenses interrogates the *same* Python
    environment that is running the audit — not an ambient global install.
    """
    proc = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json", "--with-system", "--with-urls"],
        capture_output=True, text=True, check=True)
    return json.loads(proc.stdout)


def run_audit(root: Path, packages: list[dict] | None = None) -> list[LicenseViolation]:
    """Run all three gates and return the combined violation list."""
    if packages is None:
        packages = collect_installed_licenses()
    violations: list[LicenseViolation] = []
    violations.extend(check_license_allowlist(packages))
    violations.extend(check_assets_separation(root))
    violations.extend(check_no_secrets(root))
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="ttobak-audit", description="License & security gate (spec 9.5 / 14.5).")
    parser.add_argument("--root", default=".", help="Repository root to scan (default: current directory).")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    violations = run_audit(root)
    if violations:
        print(f"FAIL: {len(violations)} license/security violation(s):")
        for v in violations:
            print(f"  [{v.kind}] {v.detail}")
        return 1
    print("PASS: license & security audit clean.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
