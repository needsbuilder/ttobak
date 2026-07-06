from pathlib import Path

import pytest
from pydantic import ValidationError

from ttobak.pictogram.models import PictogramRef
from ttobak.pictogram.lexicon import LEXICON

_ASSETS_PICTOGRAMS = Path(__file__).resolve().parents[2] / "assets" / "pictograms"


def test_pictogram_ref_fields():
    ref = PictogramRef(concept="돈", set="mulberry", glyph_id="mulberry/money.svg", caption="돈")
    assert ref.concept == "돈"
    assert ref.set == "mulberry"
    assert ref.glyph_id == "mulberry/money.svg"
    assert ref.caption == "돈"


def test_lexicon_has_core_concepts():
    assert isinstance(LEXICON, dict)
    assert len(LEXICON) >= 30
    for keyword in ("돈", "날짜", "신청", "마감", "전화", "주소", "병원", "세금"):
        assert keyword in LEXICON
        assert isinstance(LEXICON[keyword], PictogramRef)


def test_lexicon_glyphs_are_path_refs_not_inlined():
    for ref in LEXICON.values():
        assert "/" in ref.glyph_id
        assert not ref.glyph_id.startswith("data:")
        assert ref.set in {"mulberry", "openmoji"}
        assert ref.caption


# Regression: every LEXICON entry must resolve to a real file under
# assets/pictograms/, or the renderer silently shows a broken image icon
# (bug found 2026-07-06 — the lexicon shipped with zero matching asset files).
def test_lexicon_glyphs_resolve_to_real_asset_files():
    missing = sorted({
        ref.glyph_id for ref in LEXICON.values()
        if not (_ASSETS_PICTOGRAMS / ref.glyph_id).is_file()
    })
    assert not missing, f"LEXICON glyph_id(s) with no file under assets/pictograms/: {missing}"


# Regression: DISTINCT glyph_ids must resolve to DISTINCT icon files. Concepts
# that intentionally share a picture share the SAME glyph_id (돈/금액 → money.svg,
# 날짜/기한 → calendar.svg); two different glyph_ids pointing at byte-identical
# files means two concepts collapse to the same picture — defeating pictograms
# for the low-literacy reader. (Found 2026-07-06: money.svg was a byte-identical
# copy of bank.svg, so 돈·은행·계좌 all rendered as the same bank building.)
def test_distinct_glyph_ids_have_distinct_file_content():
    import hashlib

    by_hash: dict[str, list[str]] = {}
    for glyph_id in sorted({ref.glyph_id for ref in LEXICON.values()}):
        path = _ASSETS_PICTOGRAMS / glyph_id
        if not path.is_file():
            continue  # covered by the resolve-to-real-file test above
        digest = hashlib.md5(path.read_bytes()).hexdigest()
        by_hash.setdefault(digest, []).append(glyph_id)

    collisions = {h: ids for h, ids in by_hash.items() if len(ids) > 1}
    assert not collisions, (
        "distinct glyph_ids resolve to byte-identical files (same picture): "
        f"{[ids for ids in collisions.values()]}"
    )


# M4 regression: data: URI glyph_ids must be rejected at model level (spec §9.4)
def test_pictogram_ref_rejects_data_uri_glyph_id():
    """PictogramRef must raise ValidationError when glyph_id is a data: URI."""
    with pytest.raises((ValueError, ValidationError)):
        PictogramRef(
            concept="test",
            set="mulberry",
            glyph_id="data:image/svg+xml;base64,AAAA",
            caption="test",
        )


def test_pictogram_ref_rejects_data_uri_case_insensitive():
    """data: URI rejection must be case-insensitive (e.g. DATA:image/...)."""
    with pytest.raises((ValueError, ValidationError)):
        PictogramRef(
            concept="test",
            set="mulberry",
            glyph_id="DATA:image/svg+xml;base64,AAAA",
            caption="test",
        )


def test_pictogram_ref_accepts_relative_path():
    """Legitimate relative-path glyph_ids must still be accepted after M4 fix."""
    ref = PictogramRef(concept="돈", set="mulberry", glyph_id="mulberry/money.svg", caption="돈")
    assert ref.glyph_id == "mulberry/money.svg"


def test_pictogram_ref_accepts_https_url():
    """HTTPS URLs must still be accepted as glyph_ids after M4 fix."""
    ref = PictogramRef(
        concept="신청",
        set="openmoji",
        glyph_id="https://example.org/icons/apply.svg",
        caption="신청",
    )
    assert ref.glyph_id.startswith("https://")
