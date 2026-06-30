from ttobak.common import Severity
from ttobak.metric.tokenize import Token
from ttobak.metric.rules import (
    ALL_RULES,
    RuleResult,
    rule_sentence_length,
    rule_passive_ratio,
    rule_negation_ratio,
    rule_hanja_loanword_ratio,
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


def test_hanja_loanword_ratio_high_for_sino_korean_heavy():
    tokens = [Token("납부", "NNG"), Token("의무", "NNG"), Token("이행", "NNG"), Token("기한", "NNG")]
    r = rule_hanja_loanword_ratio("납부 의무 이행 기한", tokens)
    assert 0.0 <= r.sub_score <= 100.0


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
