import subprocess
from pathlib import Path

import pytest

from scripts.check_assets_separation import find_asset_leaks

ROOT = Path(__file__).resolve().parent.parent


def _git_repo(tmp_path: Path, gitignore: str) -> Path:
    """`.gitignore` 를 가진 최소 git 저장소를 만든다. git 이 없으면 skip."""
    try:
        subprocess.run(["git", "init", "-q", str(tmp_path)], check=True,
                       capture_output=True, timeout=30)
    except (OSError, subprocess.SubprocessError) as exc:  # pragma: no cover
        pytest.skip(f"git unavailable: {exc}")
    (tmp_path / ".gitignore").write_text(gitignore, encoding="utf-8")
    (tmp_path / "assets").mkdir(exist_ok=True)
    return tmp_path


def test_assets_dir_exists_with_readme():
    assert (ROOT / "assets").is_dir()
    readme = (ROOT / "assets" / "README.md").read_text(encoding="utf-8")
    assert "CC BY-SA" in readme


def test_current_repo_has_no_asset_leaks():
    assert find_asset_leaks(ROOT) == []


def test_detects_pictogram_binary_committed_outside_assets(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "assets").mkdir()
    # a pictogram glyph living in the Apache code tree = a leak
    (tmp_path / "ttobak" / "stray_glyph.svg").write_text("<svg></svg>", encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("stray_glyph.svg" in p for p in leaks)


def test_detects_base64_inlined_glyph_in_code(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "assets").mkdir()
    code = 'GLYPH = "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="\n'
    (tmp_path / "ttobak" / "render.py").write_text(code, encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("render.py" in p for p in leaks)


# Fix #1 — Rule 2 must scan ALL text files under ttobak/, not just .py
def test_detects_base64_inlined_glyph_in_non_py_file(tmp_path):
    """Data URI in an HTML template under ttobak/ must be flagged (fix #1)."""
    (tmp_path / "ttobak" / "web" / "templates").mkdir(parents=True)
    (tmp_path / "assets").mkdir()
    html = '<img src="data:image/png;base64,AAAA" />\n'
    (tmp_path / "ttobak" / "web" / "templates" / "x.html").write_text(html, encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("x.html" in p for p in leaks)


# Fix #3 — data-URI regex must be case-insensitive
def test_detects_base64_inlined_glyph_uppercase_mime(tmp_path):
    """data:image/SVG+xml;base64, (uppercase MIME) must be flagged (fix #3)."""
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "assets").mkdir()
    code = 'SRC = "data:image/SVG+xml;base64,PHN2Zz48L3N2Zz4="\n'
    (tmp_path / "ttobak" / "render.py").write_text(code, encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("render.py" in p for p in leaks)


# Fix #2 — Rule 1 breadth: pictogram committed outside assets/ anywhere in repo
def test_detects_pictogram_outside_assets_at_repo_root(tmp_path):
    """A pictogram at repo root (not in assets/) must be flagged (Rule 1 breadth)."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "logo.svg").write_text("<svg></svg>", encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("logo.svg" in p for p in leaks)


# Fix (corpus bypass, CONFIRMED) — Rule 2 scan scope must cover corpus/, not
# just ttobak/: a base64 glyph hidden in corpus/pairs.jsonl bypasses Rule 1
# entirely (.jsonl isn't a pictogram extension) and previously passed clean.
def test_detects_base64_inlined_glyph_in_corpus_jsonl(tmp_path):
    """A data URI embedded in corpus/pairs.jsonl must be flagged."""
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "assets").mkdir()
    (tmp_path / "corpus").mkdir()
    line = '{"source_text": "x", "glyph": "data:image/svg+xml;base64,PHN2Zz48L3N2Zz4="}\n'
    (tmp_path / "corpus" / "pairs.jsonl").write_text(line, encoding="utf-8")
    leaks = find_asset_leaks(tmp_path)
    assert any("pairs.jsonl" in p for p in leaks)


# Fix (corpus bypass, CONFIRMED) — root-level deployed data files (README,
# NOTICE, ...) must be scanned too, not just ttobak/.
def test_detects_base64_inlined_glyph_in_root_data_file(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "assets").mkdir()
    (tmp_path / "README.md").write_text(
        "![x](data:image/png;base64,AAAA)\n", encoding="utf-8"
    )
    leaks = find_asset_leaks(tmp_path)
    assert any("README.md" in p for p in leaks)


# Fix #4 — skip-dir matching must use relative parts, not absolute path parts
def test_skip_dirs_use_relative_parts(tmp_path):
    """build/ inside the repo is skipped; a leak elsewhere is still caught (fix #4)."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "ttobak").mkdir()
    # Contents inside repo-level build/ must be skipped (not flagged as leaks)
    (tmp_path / "build").mkdir()
    (tmp_path / "build" / "output.svg").write_text("<svg></svg>", encoding="utf-8")
    # A real leak in scripts/ must still be caught
    (tmp_path / "scripts").mkdir()
    (tmp_path / "scripts" / "logo.png").write_bytes(b"\x89PNG\r\n")
    leaks = find_asset_leaks(tmp_path)
    # build/output.svg must NOT appear (skipped)
    assert not any("output.svg" in p for p in leaks)
    # scripts/logo.png MUST appear
    assert any("logo.png" in p for p in leaks)


# ---------------------------------------------------------------------------
# gitignore 존중 (2026-07-29)
#
# 이 스캐너가 지키려는 것은 "배포되는 트리에서 CC BY-SA 픽토그램과 Apache 코드가
# 섞이지 않는가" 다. gitignore 된 파일은 정의상 배포물에 들어가지 않는다 —
# 참고자료 스크린샷, 내려받은 자료 같은 로컬 작업 파일까지 유출로 신고하면
# 거짓 경보가 나고, 진짜 유출과 구분이 안 되어 게이트가 무뎌진다.
# ---------------------------------------------------------------------------


def test_gitignored_pictogram_is_not_a_leak(tmp_path):
    """gitignore 된 이미지는 배포되지 않으므로 유출이 아니다."""
    repo = _git_repo(tmp_path, "docs/scratch/\n")
    (repo / "docs" / "scratch").mkdir(parents=True)
    (repo / "docs" / "scratch" / "reference-shot.png").write_bytes(b"\x89PNG\r\n")
    assert find_asset_leaks(repo) == []


def test_tracked_pictogram_outside_assets_is_still_a_leak(tmp_path):
    """gitignore 되지 않은 이미지는 여전히 유출이다 — 게이트를 무디게 하지 않는다."""
    repo = _git_repo(tmp_path, "docs/scratch/\n")
    (repo / "ttobak").mkdir()
    (repo / "ttobak" / "stray_glyph.svg").write_text("<svg></svg>", encoding="utf-8")
    leaks = find_asset_leaks(repo)
    assert any("stray_glyph.svg" in p for p in leaks)


def test_gitignored_data_uri_is_not_a_leak(tmp_path):
    """규칙 2(base64 인라인)도 같은 기준을 따른다."""
    repo = _git_repo(tmp_path, "ttobak/generated/\n")
    (repo / "ttobak" / "generated").mkdir(parents=True)
    (repo / "ttobak" / "generated" / "out.html").write_text(
        '<img src="data:image/png;base64,AAAA" />\n', encoding="utf-8"
    )
    assert find_asset_leaks(repo) == []


def test_non_git_directory_still_scans_everything(tmp_path):
    """git 저장소가 아니면 예전처럼 전부 검사한다(폴백이 게이트를 끄면 안 된다)."""
    (tmp_path / "assets").mkdir()
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "shot.png").write_bytes(b"\x89PNG\r\n")
    leaks = find_asset_leaks(tmp_path)
    assert any("shot.png" in p for p in leaks)


def test_gitignored_non_ascii_path_is_matched(tmp_path):
    """한글 등 비ASCII 경로도 정확히 대조된다.

    `git check-ignore` 는 -z 없이 실행하면 비ASCII 경로를 따옴표로 감싸고 8진
    이스케이프해서 출력한다("docs/\\354\\235\\274...png"). 그러면 원래 경로와
    매칭에 실패해 무시 설정이 조용히 통째로 먹히지 않는다 — 한글 경로가 많은
    이 저장소에서는 사실상 기능이 없는 것과 같다.
    """
    repo = _git_repo(tmp_path, "문서/자료/\n")
    (repo / "문서" / "자료").mkdir(parents=True)
    (repo / "문서" / "자료" / "배점표.png").write_bytes(b"\x89PNG\r\n")
    assert find_asset_leaks(repo) == []
