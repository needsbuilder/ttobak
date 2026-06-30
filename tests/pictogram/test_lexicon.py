import pytest
from pydantic import ValidationError

from ttobak.pictogram.models import PictogramRef
from ttobak.pictogram.lexicon import LEXICON


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
