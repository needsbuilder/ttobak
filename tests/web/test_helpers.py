from pathlib import Path

import pytest

from ttobak.levels import Level
from ttobak.web import app as webapp


def test_level_choices_maps_to_level_enum():
    assert set(webapp.LEVEL_CHOICES.values()) == {Level.PLAIN, Level.EASY}
    assert all(isinstance(k, str) and k for k in webapp.LEVEL_CHOICES)


def test_resolve_level_known_label():
    label = next(k for k, v in webapp.LEVEL_CHOICES.items() if v == Level.EASY)
    assert webapp._resolve_level(label) == Level.EASY


def test_resolve_level_unknown_defaults_to_easy():
    assert webapp._resolve_level("존재하지 않는 등급") == Level.EASY


def test_load_source_from_text():
    source, mime = webapp._load_source("국민건강보험료 고지서입니다.", None)
    assert source == "국민건강보험료 고지서입니다."
    assert mime == "text/plain"


def test_load_source_prefers_file_over_text(tmp_path: Path):
    f = tmp_path / "notice.pdf"
    f.write_bytes(b"%PDF-1.4 fake")
    source, mime = webapp._load_source("ignored text", str(f))
    assert source == b"%PDF-1.4 fake"
    assert mime == "application/pdf"


def test_load_source_hwpx_mime(tmp_path: Path):
    f = tmp_path / "doc.hwpx"
    f.write_bytes(b"PK\x03\x04hwpx")
    _, mime = webapp._load_source("", str(f))
    assert mime == "application/vnd.hancom.hwpx"


def test_load_source_empty_raises():
    with pytest.raises(ValueError):
        webapp._load_source("   ", None)
