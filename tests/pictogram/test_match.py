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


# Bug regression: '약' (medicine, 1-syllable keyword) must not match inside
# unrelated compound words that happen to contain the same syllable.
def test_match_does_not_overmatch_medicine_inside_contract_words():
    text = "이 계약은 예약과 요약본이며 절약과 약간의 차이가 있습니다."
    refs = match(text)
    assert "mulberry/medicine.svg" not in {r.glyph_id for r in refs}


def test_match_does_not_overmatch_medicine_inside_promise_words():
    text = "약속과 약관, 규약, 공약, 조약도 마찬가지입니다."
    refs = match(text)
    assert "mulberry/medicine.svg" not in {r.glyph_id for r in refs}


def test_match_still_matches_medicine_for_legit_usage_with_particle():
    refs = match("약을 드세요.")
    assert "mulberry/medicine.svg" in {r.glyph_id for r in refs}


def test_match_still_matches_medicine_for_legit_usage_with_space():
    refs = match("약 복용 방법을 확인하세요.")
    assert "mulberry/medicine.svg" in {r.glyph_id for r in refs}


def test_match_finds_medicine_after_skipping_false_positive_occurrence():
    """첫 등장이 오탐 복합어여도 뒤에 정상 용례가 있으면 매칭돼야 한다."""
    refs = match("이 계약은 중요합니다. 약을 꼭 챙겨 드세요.")
    assert "mulberry/medicine.svg" in {r.glyph_id for r in refs}
