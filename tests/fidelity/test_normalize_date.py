from datetime import date

import pytest

from ttobak.fidelity.normalize import normalize_date, normalize_phone

REF = date(2026, 7, 10)


@pytest.mark.parametrize(
    "text,iso,inclusive",
    [
        ("2026년 7월 17일까지", "2026-07-17", True),
        ("2026년 7월 17일", "2026-07-17", False),
        ("2026-07-17", "2026-07-17", False),
        ("2026.07.17", "2026-07-17", False),
        ("2026년 7월 17일 전까지", "2026-07-17", False),
        ("D-7", "2026-07-17", False),
        ("7일 후", "2026-07-17", False),
    ],
)
def test_normalize_date(text, iso, inclusive):
    got_iso, got_inclusive = normalize_date(text, REF)
    assert got_iso == iso
    assert got_inclusive is inclusive


@pytest.mark.parametrize(
    "text,expected",
    [
        ("02-1234-5678", "0212345678"),
        ("010 1234 5678", "01012345678"),
        ("☎ 1577-1000", "15771000"),
        ("(02)123-4567", "021234567"),
    ],
)
def test_normalize_phone(text, expected):
    assert normalize_phone(text) == expected
