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
