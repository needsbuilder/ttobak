from ttobak.fidelity.negation_guard import check_negation_flip, scan_negations


def test_scan_negations_finds_markers():
    found = scan_negations("외국인은 신청 대상에서 제외됩니다.")
    assert "제외" in found


def test_scan_negations_multiple():
    found = scan_negations("신청할 수 없으며 환불은 불가합니다.")
    assert "없" in found
    assert "불가" in found


def test_negation_dropped_is_flagged():
    src = "외국인은 지원 대상에서 제외됩니다."
    easy = "외국인도 지원 대상에 포함됩니다."
    flips = check_negation_flip(src, easy)
    assert flips != []
    assert any("제외" in f for f in flips)


def test_clean_negation_preserved_no_flip():
    src = "외국인은 지원 대상에서 제외됩니다."
    easy = "외국인은 지원을 받을 수 없습니다. 외국인은 대상에서 제외됩니다."
    flips = check_negation_flip(src, easy)
    assert flips == []


def test_no_source_negation_no_flip():
    src = "모든 국민이 신청할 수 있습니다."
    easy = "누구나 신청할 수 있습니다."
    assert check_negation_flip(src, easy) == []
