from datetime import date

from ttobak.eval.distortion_bench import DistortionCase, DistortionType, generate_distortions

SOURCE = (
    "건강보험료 1,295,400원을 2026년 7월 17일까지 강서구청에 납부하십시오. "
    "지원금은 3억 원이며 만 65세 이상은 제외됩니다. 소득 30,000원 미만이어야 합니다."
)
EASY = (
    "건강보험료 1,295,400원을 2026년 7월 17일까지 강서구청에 내세요. "
    "지원금은 3억 원이고 만 65세 이상은 빠집니다. 소득 30,000원 미만이어야 합니다."
)


def test_returns_distortioncases():
    cases = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1))
    assert cases and all(isinstance(c, DistortionCase) for c in cases)


def test_includes_exactly_one_clean_control_unchanged():
    cases = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1))
    cleans = [c for c in cases if c.distortion_type == DistortionType.CLEAN]
    assert len(cleans) == 1
    assert cleans[0].is_clean is True and cleans[0].expected_pass is True
    assert cleans[0].distorted_text == EASY


def test_distorted_cases_are_labeled_and_mutated():
    cases = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1))
    distorted = [c for c in cases if c.distortion_type != DistortionType.CLEAN]
    assert distorted
    for c in distorted:
        assert c.is_clean is False and c.expected_pass is False
        assert c.distorted_text != c.easy_text


def test_number_swap_changes_a_number():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.NUMBER_SWAP)
    assert "30,000원" not in c.distorted_text and "3,000원" in c.distorted_text


def test_digit_drop_loses_a_digit():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.DIGIT_DROP)
    assert "1,295,400" not in c.distorted_text and "129,540" in c.distorted_text


def test_krw_unit_error_downgrades_eok():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.KRW_UNIT_ERROR)
    assert "3억" not in c.distorted_text and "3천만" in c.distorted_text


def test_date_shift_changes_the_day():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.DATE_SHIFT)
    assert "7월 17일" not in c.distorted_text and "7월 7일" in c.distorted_text


def test_negation_drop_removes_exclusion():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.NEGATION_DROP)
    assert "빠집니다" not in c.distorted_text and "포함됩니다" in c.distorted_text


def test_condition_flip_inverts_boundary():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.CONDITION_FLIP)
    assert "이상" not in c.distorted_text and "이하" in c.distorted_text


def test_range_weaken_softens_boundary():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.RANGE_WEAKEN)
    assert "미만" not in c.distorted_text and "이하" in c.distorted_text


def test_entity_swap_replaces_agency():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.ENTITY_SWAP)
    assert "강서구청" not in c.distorted_text and "송파구청" in c.distorted_text


def test_hallucinated_entity_adds_unsourced_agency():
    c = next(c for c in generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1)) if c.distortion_type == DistortionType.HALLUCINATED_ENTITY)
    assert "국민건강보험공단" in c.distorted_text and "국민건강보험공단" not in c.easy_text


def test_deterministic_for_same_seed():
    a = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1), seed=7)
    b = generate_distortions(SOURCE, EASY, ref_date=date(2026, 7, 1), seed=7)
    assert [c.model_dump() for c in a] == [c.model_dump() for c in b]
