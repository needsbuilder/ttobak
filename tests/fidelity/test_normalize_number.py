import pytest

from ttobak.fidelity.normalize import normalize_korean_number, normalize_money


@pytest.mark.parametrize(
    "text,expected",
    [
        ("삼만원", 30000),
        ("3만5천원", 35000),
        ("3만 5천 원", 35000),
        ("약 3억 원", 300000000),
        ("일십이만삼천사백오십육", 123456),
        ("1억 2천만", 120000000),
        ("천이백구십오만", 12950000),
        ("100", 100),
        ("1,295,400", 1295400),
        ("오천", 5000),
        ("이천이십육", 2026),
    ],
)
def test_normalize_korean_number(text, expected):
    assert normalize_korean_number(text) == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("1,295,400원", 1295400),
        ("삼만원", 30000),
        ("약 3억 원", 300000000),
        ("금 1,200,000원정", 1200000),
        ("3만5천원", 35000),
    ],
)
def test_normalize_money(text, expected):
    assert normalize_money(text) == expected
