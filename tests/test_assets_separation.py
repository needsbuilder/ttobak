from pathlib import Path

from scripts.check_assets_separation import find_asset_leaks

ROOT = Path(__file__).resolve().parent.parent


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
