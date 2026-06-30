"""Ttobak license & security audit gate (spec 9.5 / 14.5).

Deterministic checks that fail the build on: GPL/AGPL/NC/proprietary code deps;
pictogram CC BY-SA assets leaking out of /assets; secrets/PII committed. The
license check operates on parsed `pip-licenses --format=json` output so it is
unit-testable with planted fixtures.
"""
from __future__ import annotations

from dataclasses import dataclass


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
