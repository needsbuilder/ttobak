import pytest

from ttobak.metric.tokenize import Token
from ttobak.metric.rules import (
    ALL_RULES,
    RuleResult,
    rule_sentence_length,
    rule_passive_ratio,
    rule_negation_ratio,
    rule_hanja_loanword_ratio,
    rule_undefined_hard_term,
    rule_abbrev_percent_bignum,
)


def test_ruleresult_shape():
    r = rule_sentence_length("짧다.", [Token("짧", "VA"), Token("다", "EF")])
    assert isinstance(r, RuleResult)
    assert 0.0 <= r.sub_score <= 100.0
    assert isinstance(r.violations, list)


def test_long_sentence_scores_lower_than_short():
    short = rule_sentence_length("내세요.", [Token("내", "VV"), Token("세요", "EF")])
    long_text = " ".join(["아주"] * 40) + " 납부하여야 합니다."
    long_tokens = [Token("아주", "MAG")] * 40 + [Token("납부", "NNG"), Token("하", "XSV"), Token("여야", "EC"), Token("합니다", "VX")]
    long = rule_sentence_length(long_text, long_tokens)
    assert long.sub_score < short.sub_score
    assert long.violations  # a long sentence raises at least one violation


def test_passive_ratio_flags_passive_suffix():
    # 처리되다 — 피동 (passive). One passive predicate should be flagged.
    tokens = [Token("처리", "NNG"), Token("되", "XSV"), Token("ㅂ니다", "EF")]
    r = rule_passive_ratio("처리됩니다.", tokens)
    assert any("처리" in v.span or v.rule == "passive_ratio" for v in r.violations)


def test_negation_ratio_flags_negation():
    tokens = [Token("신청", "NNG"), Token("할", "ETM"), Token("수", "NNB"), Token("없", "VA"), Token("습니다", "EF")]
    r = rule_negation_ratio("신청할 수 없습니다.", tokens)
    assert r.violations


def test_negation_ratio_flags_anh_contracted_form():
    """Regression: '않' (contracted ~아니하다) must be detected as negation (R-06 false-negative fix)."""
    # 내지 않으면 돈을 더 내야 합니다 — '않' is the dominant colloquial negation form
    tokens = [
        Token("내지", "VV"),
        Token("않", "VX"),
        Token("으면", "EC"),
        Token("돈", "NNG"),
        Token("을", "JKO"),
        Token("더", "MAG"),
        Token("내야", "VV"),
        Token("합니다", "VX"),
    ]
    r = rule_negation_ratio("내지 않으면 돈을 더 내야 합니다.", tokens)
    assert r.violations, "'않' should be flagged as a negation lexeme"


def test_hanja_loanword_ratio_high_for_sino_korean_heavy():
    """R-03: Sino-Korean heavy text must score lower than native Korean nouns."""
    # Sino-Korean admin vocabulary (all in hard_terms.txt)
    sino_tokens = [Token("납부", "NNG"), Token("의무", "NNG"), Token("이행", "NNG"), Token("산정", "NNG")]
    r_sino = rule_hanja_loanword_ratio("납부 의무 이행 산정", sino_tokens)

    # Native Korean nouns (not in hard_terms.txt)
    native_tokens = [Token("돈", "NNG"), Token("집", "NNG"), Token("물", "NNG"), Token("밥", "NNG")]
    r_native = rule_hanja_loanword_ratio("돈 집 물 밥", native_tokens)

    assert r_sino.sub_score < r_native.sub_score, (
        f"Sino-Korean heavy text ({r_sino.sub_score}) should score lower "
        f"than native Korean nouns ({r_native.sub_score})"
    )


def test_all_rules_is_list_of_name_fn_pairs():
    assert isinstance(ALL_RULES, list)
    names = {name for name, _ in ALL_RULES}
    for expected in (
        "sentence_length", "hard_word_ratio", "hanja_loanword_ratio",
        "predicates_connectives", "passive_ratio", "negation_ratio",
        "undefined_hard_term", "idiom", "abbrev_percent_bignum",
        "third_person_fictional", "direct_address", "modifier_ttr",
    ):
        assert expected in names
    for _name, fn in ALL_RULES:
        assert callable(fn)


# M5 regression: parenthetical-exemption logic in R-07 (undefined_hard_term)
def test_undefined_hard_term_glossed_term_yields_zero_violations():
    """R-07: '납부(돈을 내는 것)' is correctly glossed → must yield 0 violations."""
    text = "납부(돈을 내는 것)를 하세요."
    tokens = [Token("납부", "NNG")]
    r = rule_undefined_hard_term(text, tokens)
    assert r.violations == [], (
        f"Glossed hard term '납부(돈을 내는 것)' must yield 0 violations, got: {r.violations}"
    )


def test_undefined_hard_term_bare_term_yields_violation():
    """R-07: bare '납부하세요' without gloss must still yield a violation."""
    text = "납부하세요."
    tokens = [Token("납부", "NNG")]
    r = rule_undefined_hard_term(text, tokens)
    assert r.violations, "Bare hard term '납부' without gloss must yield a violation"


# ---------------------------------------------------------------------------
# Bug fix regression tests (adversarially-confirmed bugs, fixed via TDD)
# ---------------------------------------------------------------------------


def test_passive_ratio_detects_kiwi_stem_forms():
    """R-05 bug fix: kiwipiepy 0.23.x emits stem forms for passive predicates
    (당하/VV, 받/VV-R, 되/XSV), not the dictionary forms (당하다/받다/지다) that
    _PASSIVE_FORMS previously matched against, so only '되' was ever detected.
    All three real-world passive constructions must now be flagged."""
    cases = [
        ("신청인은 처벌을 당했다.", [
            Token("신청인", "NNG"), Token("은", "JX"), Token("처벌", "NNG"), Token("을", "JKO"),
            Token("당하", "VV"), Token("었", "EP"), Token("다", "EF"), Token(".", "SF"),
        ]),
        ("서류는 접수받았다.", [
            Token("서류", "NNG"), Token("는", "JX"), Token("접수", "NNG"),
            Token("받", "VV-R"), Token("었", "EP"), Token("다", "EF"), Token(".", "SF"),
        ]),
        ("지원금은 지급된다.", [
            Token("지원금", "NNG"), Token("은", "JX"), Token("지급", "NNG"),
            Token("되", "XSV"), Token("ᆫ다", "EF"), Token(".", "SF"),
        ]),
    ]
    for text, tokens in cases:
        r = rule_passive_ratio(text, tokens)
        assert r.violations, f"'{text}' should be flagged as passive, got no violations"


def test_passive_ratio_denominator_counts_irregular_verb_tags():
    """R-05/verb-tag bug fix: _VERB_TAGS exact-matched 'VV'/'VA'/'XSV', but kiwipiepy
    emits irregular-conjugation variants (VV-R/VV-I/VA-I) that never satisfied the
    exact match, undercounting the denominator and inflating the passive ratio.
    Prefix-matching (tag.split('-')[0]) must count all 4 verb tokens below, of which
    only 1 ('되') is passive, giving ratio 0.25 (partial score) instead of a false 1.0."""
    tokens = [
        Token("춥", "VA-I"), Token("다", "EF"),
        Token("걷", "VV-I"), Token("는다", "EF"),
        Token("먹", "VV"), Token("는다", "EF"),
        Token("처리", "NNG"), Token("되", "XSV"), Token("ㅂ니다", "EF"),
    ]
    r = rule_passive_ratio("춥다. 걷는다. 먹는다. 처리됩니다.", tokens)
    assert r.sub_score == pytest.approx(62.5), (
        f"expected partial score for 1/4 passive ratio, got {r.sub_score}"
    )


def test_bignum_comma_and_plain_digits_agree():
    """R-09 bug fix: _BIGNUM_RE counted comma characters toward the '≥6 significant
    digits' threshold, so '30,000' (only 5 significant digits, value 30,000 <
    100,000) was wrongly flagged while the equivalent '30000' was not. Strip commas
    before counting digits so both forms agree (neither should be flagged)."""
    r_comma = rule_abbrev_percent_bignum("30,000원을 내야 합니다.", [])
    r_plain = rule_abbrev_percent_bignum("30000원을 내야 합니다.", [])
    assert r_comma.sub_score == r_plain.sub_score == 100.0
    assert r_comma.violations == [] and r_plain.violations == []


def test_bignum_seven_digit_comma_form_still_flagged():
    """R-09: a genuinely large number (7 significant digits, ≥100,000) must still
    be flagged as a violation even when comma-grouped."""
    r = rule_abbrev_percent_bignum("1,295,400원을 내야 합니다.", [])
    assert any("1,295,400" in v.span for v in r.violations)


def test_undefined_hard_term_occurrence_before_gloss_is_violation():
    """R-07 bug fix: _is_glossed() checked the whole text globally, so a bare use of
    a term appearing BEFORE its later parenthetical gloss was wrongly exempted.
    Only occurrences at/after the first gloss position should be exempt; earlier
    bare uses must be flagged as violations."""
    text = "납부를 먼저 하세요. 그리고 납부(돈을 내는 것)를 또 하세요."
    tokens = [Token("납부", "NNG"), Token("납부", "NNG")]
    r = rule_undefined_hard_term(text, tokens)
    assert r.violations, "occurrence of '납부' before its gloss must be flagged"


def test_undefined_hard_term_reappearance_after_gloss_stays_exempt():
    """R-07: once a term is glossed, later bare reuse of the same term is fine per
    easy-read guidance (explain once, reuse freely) — must remain exempt."""
    text = "납부(돈을 내는 것)를 하세요. 다음 달에도 납부를 계속하세요."
    tokens = [Token("납부", "NNG"), Token("납부", "NNG")]
    r = rule_undefined_hard_term(text, tokens)
    assert r.violations == [], "term reused after its first gloss should remain exempt"
