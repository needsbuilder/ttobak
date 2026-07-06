from pathlib import Path

from tooling.check_licenses import check_assets_separation


def _make_clean_tree(root: Path) -> None:
    (root / "ttobak" / "pictogram").mkdir(parents=True)
    (root / "ttobak" / "pictogram" / "__init__.py").write_text("", encoding="utf-8")
    assets = root / "assets" / "pictograms"
    (assets / "mulberry").mkdir(parents=True)
    (assets / "openmoji").mkdir(parents=True)
    (assets / "mulberry" / "LICENSE").write_text("CC BY-SA 2.0 UK", encoding="utf-8")
    (assets / "openmoji" / "LICENSE").write_text("CC BY-SA 4.0", encoding="utf-8")
    (assets / "mulberry" / "phone.svg").write_text("<svg/>", encoding="utf-8")
    (assets / "openmoji" / "1F4B0.svg").write_text("<svg/>", encoding="utf-8")


def test_clean_tree_passes(tmp_path):
    _make_clean_tree(tmp_path)
    assert check_assets_separation(tmp_path) == []


def test_glyph_leaked_into_code_tree_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "ttobak" / "pictogram" / "leaked.svg").write_text("<svg/>", encoding="utf-8")
    violations = check_assets_separation(tmp_path)
    assert any(v.kind == "asset-leak" for v in violations)
    assert any("leaked.svg" in v.detail for v in violations)


def test_base64_glyph_embedded_in_code_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "ttobak" / "pictogram" / "embed.py").write_text(
        'GLYPH = "data:image/svg+xml;base64,PHN2Zy8+"\n', encoding="utf-8")
    assert any(v.kind == "asset-embed" for v in check_assets_separation(tmp_path))


def test_pictogram_set_missing_license_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "assets" / "pictograms" / "mulberry" / "LICENSE").unlink()
    violations = check_assets_separation(tmp_path)
    assert any(v.kind == "asset-missing-license" for v in violations)
    assert any("mulberry" in v.detail for v in violations)


def test_glyph_leaked_into_corpus_is_flagged(tmp_path):
    _make_clean_tree(tmp_path)
    (tmp_path / "corpus").mkdir()
    (tmp_path / "corpus" / "stray.png").write_bytes(b"\x89PNG\r\n")
    assert any(v.kind == "asset-leak" for v in check_assets_separation(tmp_path))


def test_jpg_glyph_leaked_into_code_tree_is_flagged(tmp_path):
    """.jpg/.jpeg must be caught too — GLYPH_SUFFIXES was out of sync with the
    sister gate and let JPEG glyphs pass local audit (fixed 2026-07-06)."""
    _make_clean_tree(tmp_path)
    (tmp_path / "ttobak" / "pictogram" / "leaked.jpg").write_bytes(b"\xff\xd8\xff")
    assert any(v.kind == "asset-leak" and "leaked.jpg" in v.detail
               for v in check_assets_separation(tmp_path))


def test_svg_with_script_is_flagged(tmp_path):
    """A shipped SVG carrying <script> is active-content and must be rejected."""
    _make_clean_tree(tmp_path)
    (tmp_path / "assets" / "pictograms" / "openmoji" / "evil.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        encoding="utf-8")
    violations = check_assets_separation(tmp_path)
    assert any(v.kind == "asset-svg-active-content" and "evil.svg" in v.detail
               for v in violations)


def test_svg_with_event_handler_is_flagged(tmp_path):
    """An inline on*= event handler in a shipped SVG must be rejected."""
    _make_clean_tree(tmp_path)
    (tmp_path / "assets" / "pictograms" / "mulberry" / "evil2.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><rect onload="steal()"/></svg>',
        encoding="utf-8")
    assert any(v.kind == "asset-svg-active-content"
               for v in check_assets_separation(tmp_path))
