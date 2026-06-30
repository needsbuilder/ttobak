from ttobak.pictogram import match
from ttobak.pictogram.models import PictogramRef


def test_match_returns_refs_for_known_concepts():
    text = "신청 서류를 7월에 우편으로 보내세요. 전화로 물어볼 수 있어요."
    refs = match(text)
    glyphs = {r.glyph_id for r in refs}
    assert "mulberry/apply.svg" in glyphs
    assert "mulberry/document.svg" in glyphs
    assert "mulberry/mail.svg" in glyphs
    assert "mulberry/phone.svg" in glyphs
    assert all(isinstance(r, PictogramRef) for r in refs)


def test_match_empty_when_no_concept():
    assert match("오늘은 맑고 바람이 시원합니다.") == []


def test_match_deduplicates_synonyms_by_glyph():
    refs = match("돈 금액을 확인하세요.")
    money = [r for r in refs if r.glyph_id == "mulberry/money.svg"]
    assert len(money) == 1


def test_match_preserves_first_seen_order():
    refs = match("전화 신청")
    glyphs = [r.glyph_id for r in refs]
    assert glyphs.index("mulberry/phone.svg") < glyphs.index("mulberry/apply.svg")
