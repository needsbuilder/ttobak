from enum import Enum

from ttobak.levels import Level


def test_level_is_str_enum_with_exact_values():
    assert issubclass(Level, str)
    assert issubclass(Level, Enum)
    assert Level.PLAIN.value == "plain"
    assert Level.EASY.value == "easy"
    assert {m.value for m in Level} == {"plain", "easy"}


def test_level_member_equals_its_string_value():
    assert Level.EASY == "easy"
