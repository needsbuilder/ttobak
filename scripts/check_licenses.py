"""pip-licenses allowlist gate (spec §14.5 / §9.5).

Fails the build if any installed dependency carries a copyleft (GPL/AGPL) or
non-commercial (NC) license, or a license that is neither allow- nor deny-listed
(treated as "review needed"). Run in CI; `main()` returns a nonzero exit code on
any violation.
"""

from __future__ import annotations

import json
import subprocess
import sys

# Permissive + weak-copyleft-as-separate-dep licenses we ship against (spec §9.1).
ALLOWLIST: set[str] = {
    "mit",
    "bsd",
    "apache",
    "psf",
    "python software foundation",
    "isc",
    "mpl",
    "mozilla public license",
    "lgpl",  # kiwipiepy: LGPL used as a separate, unmodified dependency
    "unlicense",
    "zlib",
    "historical permission notice and warning",
}

# Substrings that are HARD blockers (spec §9.5). Checked before the allowlist.
DENYLIST_SUBSTR: set[str] = {
    "agpl",
    "affero",
    "gpl",  # plain GPL (KoNLPy etc.); the matcher below excludes LGPL
    "non-commercial",
    "noncommercial",
    "-nc-",
    "nc-sa",
    "by-nc",
    "exaone",
}


def _normalize(license_str: str) -> str:
    return (license_str or "").strip().lower()


def _is_denied(norm: str) -> bool:
    for bad in DENYLIST_SUBSTR:
        if bad == "gpl":
            # Match GPL but NOT LGPL: a "gpl" not immediately preceded by "l".
            idx = norm.find("gpl")
            while idx != -1:
                preceded_by_l = idx > 0 and norm[idx - 1] == "l"
                if not preceded_by_l:
                    return True
                idx = norm.find("gpl", idx + 1)
        elif bad in norm:
            return True
    return False


def _is_allowed(norm: str) -> bool:
    return any(good in norm for good in ALLOWLIST)


def check_licenses(
    packages: list[dict], allowlist: set[str], denylist: set[str]
) -> list[str]:
    violations: list[str] = []
    for pkg in packages:
        name = pkg.get("Name", "<unknown>")
        raw = pkg.get("License", "")
        norm = _normalize(raw)
        if _is_denied(norm):
            violations.append(f"{name}: DENIED license '{raw}'")
            continue
        if not _is_allowed(norm):
            violations.append(f"{name}: license '{raw}' not on allowlist (review needed)")
    return violations


def main() -> int:
    proc = subprocess.run(
        [sys.executable, "-m", "piplicenses", "--format=json"],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        print("pip-licenses failed to run:", file=sys.stderr)
        print(proc.stderr, file=sys.stderr)
        return 2
    packages = json.loads(proc.stdout)
    violations = check_licenses(packages, ALLOWLIST, DENYLIST_SUBSTR)
    if violations:
        print("License gate FAILED (spec §9.5 forbids GPL/AGPL/NC):", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        return 1
    print(f"License gate passed: {len(packages)} packages, all allowlisted.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
