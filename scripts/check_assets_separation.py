"""Assets separation check (spec §8.5 / §9.4).

Ensures CC BY-SA pictogram assets stay out of the Apache-2.0 `ttobak/` code tree:
  1. No pictogram binary (svg/png/jpg/jpeg/gif/webp) committed outside `assets/`.
  2. No base64/data-URI inlined glyph embedded inside `ttobak/` source files.

Used by tests and by CI (spec §14.5). `find_asset_leaks` returns the offending
paths (relative to repo root); an empty list means separation is clean.
"""

from __future__ import annotations

import re
from pathlib import Path

PICTOGRAM_EXTS = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".webp"}
_DATA_URI = re.compile(r"data:image/[a-z.+-]+;base64,", re.IGNORECASE)
_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "build", "dist"}


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

        # Rule 2: no base64/data-URI inlined glyph inside the ttobak/ code tree.
        # Scans ALL readable text files (not just .py) — a data URI in an
        # HTML template, JS module, CSS file, etc. is equally a leak.
        if rel.parts and rel.parts[0] == "ttobak":
            try:
                text = path.read_text(encoding="utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            if _DATA_URI.search(text):
                leaks.append(str(rel))

    return sorted(leaks)
