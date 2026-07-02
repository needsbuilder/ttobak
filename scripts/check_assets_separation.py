"""Assets separation check (spec §8.5 / §9.4).

Ensures CC BY-SA pictogram assets stay out of the Apache-2.0 `ttobak/` code tree:
  1. No pictogram binary (svg/png/jpg/jpeg/gif/webp) committed outside `assets/`.
  2. No base64/data-URI inlined glyph embedded inside deployed text — scanned
     across `ttobak/`, `corpus/`, and root-level data files (README, NOTICE,
     ...), not just `ttobak/`. corpus/ must be in scope: a base64 glyph
     hidden in `corpus/pairs.jsonl` bypasses rule 1 entirely (`.jsonl` isn't
     a pictogram extension) and previously shipped clean (CONFIRMED bypass).

Used by tests and by CI (spec §14.5). `find_asset_leaks` returns the offending
paths (relative to repo root); an empty list means separation is clean.
"""

from __future__ import annotations

import re
from pathlib import Path

PICTOGRAM_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
_DATA_URI = re.compile(r"data:image/[a-z.+-]+;base64,", re.IGNORECASE)
_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "build", "dist"}

# Rule 2 scan scope: deployed text under these top-level dirs, plus any file
# living directly at the repo root (README.md, NOTICE, ...). Deliberately
# excludes assets/ — that's the designated home for legitimate pictogram
# files, so a data URI found there is not a separation leak.
_DATA_URI_SCAN_TOP_DIRS = {"ttobak", "corpus"}


def _iter_files(root: Path):
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        # Use RELATIVE parts so skip-dir names in the repo's ancestor path
        # (e.g. cloned under /home/user/build/...) don't cause silent misses.
        rel_parts = path.relative_to(root).parts
        if any(part in _SKIP_DIRS or part.endswith(".egg-info") for part in rel_parts):
            continue
        yield path


def find_asset_leaks(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    assets_dir = root / "assets"
    leaks: list[str] = []

    for path in _iter_files(root):
        rel = path.relative_to(root)
        in_assets = assets_dir in path.parents

        # Rule 1: pictogram binaries must live under assets/ only.
        if path.suffix.lower() in PICTOGRAM_EXTS and not in_assets:
            leaks.append(str(rel))
            continue

        # Rule 2: no base64/data-URI inlined glyph in deployed text. Scans
        # ALL readable text files (not just .py) under ttobak/ and corpus/,
        # plus root-level data files — a data URI in an HTML template, JS
        # module, CSV/JSONL corpus row, README, etc. is equally a leak.
        in_scan_scope = (
            (rel.parts and rel.parts[0] in _DATA_URI_SCAN_TOP_DIRS)
            or len(rel.parts) == 1
        )
        if in_scan_scope:
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if _DATA_URI.search(text):
                leaks.append(str(rel))

    return sorted(leaks)
