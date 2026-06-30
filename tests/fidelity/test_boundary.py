from ttobak.fidelity.normalize import BOUNDARY_OPERATORS, detect_boundary


def test_boundary_table_exact_mapping():
    assert BOUNDARY_OPERATORS["이상"] == ">="
    assert BOUNDARY_OPERATORS["초과"] == ">"
    assert BOUNDARY_OPERATORS["이하"] == "<="
    assert BOUNDARY_OPERATORS["미만"] == "<"
    assert BOUNDARY_OPERATORS["까지"] == "inclusive"
    assert BOUNDARY_OPERATORS["부터"] == "from"


def test_detect_boundary_in_span():
    assert detect_boundary("만 65세 이상") == ">="
    assert detect_boundary("소득 300만원 미만") == "<"
    assert detect_boundary("2026년 7월 17일까지") == "inclusive"
    assert detect_boundary("정원 100명") is None


def test_미만_is_not_이하():
    # boundary weakening guard: 미만 (<) must never normalize to 이하 (<=)
    assert detect_boundary("미만") != detect_boundary("이하")
