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
