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
import subprocess
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


def _gitignored(root: Path, paths: list[Path]) -> set[Path]:
    """``paths`` 중 git 이 무시하는 것들의 집합.

    이 검사가 지키려는 것은 배포되는 트리의 라이선스 분리다. gitignore 된 파일은
    정의상 배포물에 들어가지 않으므로 유출일 수 없다 — 로컬 참고자료 스크린샷
    따위를 유출로 신고하면 거짓 경보가 나고 게이트가 무뎌진다.

    git 이 없거나 저장소가 아니면 **빈 집합**을 돌려준다. 즉 아무것도 면제되지
    않고 예전처럼 전부 검사한다 — 폴백이 게이트를 끄면 안 된다.
    """
    if not paths:
        return set()
    try:
        # -z 는 필수다. 이것 없이는 git 이 비ASCII 경로를 따옴표로 감싸고
        # 8진 이스케이프해서 내보내(예: "docs/\354\235\274\354\240\225.png")
        # 원래 경로와 대조가 되지 않는다 — 한글 경로가 조용히 전부 어긋난다.
        # -z 를 주면 입출력 모두 NUL 구분이 되고, 공백·개행이 든 경로도 안전하다.
        proc = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-z", "--stdin"],
            input="\0".join(str(p) for p in paths),
            capture_output=True,
            text=True,
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return set()
    # 0 = 일부가 무시됨, 1 = 무시되는 것 없음. 그 밖(128 = git 저장소 아님 등)은
    # 판단 불가로 보고 아무것도 면제하지 않는다.
    if proc.returncode not in (0, 1):
        return set()
    return {Path(entry) for entry in proc.stdout.split("\0") if entry}


def find_asset_leaks(repo_root: Path | str) -> list[str]:
    root = Path(repo_root).resolve()
    assets_dir = root / "assets"
    leaks: list[str] = []

    candidates = list(_iter_files(root))
    ignored = _gitignored(root, candidates)

    for path in candidates:
        if path in ignored:
            continue
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
