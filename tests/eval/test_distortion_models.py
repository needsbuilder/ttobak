from ttobak.eval.distortion_bench import DistortionCase, DistortionType


def test_taxonomy_has_ten_distortions_plus_clean():
    members = set(DistortionType)
    assert len(members) == 11
    assert DistortionType.CLEAN in members
    assert len(members - {DistortionType.CLEAN}) == 10


def test_taxonomy_exact_members():
    assert DistortionType.NUMBER_SWAP.value == "number_swap"
    assert DistortionType.DIGIT_DROP.value == "digit_drop"
    assert DistortionType.KRW_UNIT_ERROR.value == "krw_unit_error"
    assert DistortionType.DATE_SHIFT.value == "date_shift"
    assert DistortionType.INCLUSIVITY_FLIP.value == "inclusivity_flip"
    assert DistortionType.NEGATION_DROP.value == "negation_drop"
    assert DistortionType.CONDITION_FLIP.value == "condition_flip"
    assert DistortionType.RANGE_WEAKEN.value == "range_weaken"
    assert DistortionType.ENTITY_SWAP.value == "entity_swap"
    assert DistortionType.HALLUCINATED_ENTITY.value == "hallucinated_entity"


def test_clean_case_expects_pass():
    case = DistortionCase(
        case_id="p1-clean", source_text="납부 금액은 30,000원입니다.",
        easy_text="내야 할 돈은 30,000원입니다.", distorted_text="내야 할 돈은 30,000원입니다.",
        distortion_type=DistortionType.CLEAN, is_clean=True, expected_pass=True)
    assert case.is_clean is True
    assert case.expected_pass is True


def test_distorted_case_expects_not_pass():
    case = DistortionCase(
        case_id="p1-number_swap", source_text="납부 금액은 30,000원입니다.",
        easy_text="내야 할 돈은 30,000원입니다.", distorted_text="내야 할 돈은 3,000원입니다.",
        distortion_type=DistortionType.NUMBER_SWAP, is_clean=False, expected_pass=False)
    assert case.is_clean is False
    assert case.expected_pass is False
