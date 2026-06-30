from ttobak.levels import Level
from ttobak.metric import score
from ttobak.metric.models import KERReport


HARD = "장기요양보험료의 납부 의무를 이행하지 아니한 가입자에 대하여는 소득인정액에 따라 연체금이 부과될 수 있으며 경감 대상에서 제외됩니다."
EASY = "보험료를 내야 합니다.\n내지 않으면 돈을 더 내야 합니다.\n7월 17일까지 내세요."


def test_score_returns_kerreport_in_range():
    r = score(EASY, Level.EASY)
    assert isinstance(r, KERReport)
    assert 0.0 <= r.score <= 100.0
    assert r.level_estimate in (1, 2, 3)
    assert isinstance(r.sub_scores, dict) and r.sub_scores


def test_sub_scores_have_one_entry_per_rule():
    from ttobak.metric.rules import ALL_RULES
    r = score(EASY, Level.EASY)
    assert set(r.sub_scores.keys()) == {name for name, _ in ALL_RULES}


def test_easy_text_scores_higher_than_hard_text():
    easy = score(EASY, Level.EASY)
    hard = score(HARD, Level.EASY)
    assert easy.score > hard.score
    # the hard text raises more rule violations than the easy one
    assert len(hard.violations) >= len(easy.violations)
