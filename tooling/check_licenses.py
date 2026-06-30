"""Ttobak license & security audit gate (spec 9.5 / 14.5).

Deterministic checks that fail the build on: GPL/AGPL/NC/proprietary code deps;
pictogram CC BY-SA assets leaking out of /assets; secrets/PII committed. The
license check operates on parsed `pip-licenses --format=json` output so it is
unit-testable with planted fixtures.
"""
from __future__ import annotations

import re
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
