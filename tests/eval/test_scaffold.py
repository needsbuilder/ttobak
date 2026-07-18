from datetime import date

import ttobak.eval
from ttobak.ir import BlockType, Document


def test_eval_package_importable():
    assert ttobak.eval.__name__ == "ttobak.eval"


def test_sample_document_fixture(sample_document):
    assert isinstance(sample_document, Document)
    assert sample_document.source_mime == "text/plain"
    assert "1,295,400원" in sample_document.text()
    assert any(b.type == BlockType.HEADING for b in sample_document.blocks)


def test_ref_date_fixture(ref_date):
    assert ref_date == date(2026, 7, 1)


def test_fake_provider_is_deterministic(fake_provider):
    out_a = fake_provider.generate("아무 프롬프트")
    out_b = fake_provider.generate("아무 프롬프트")
    assert out_a == out_b
    assert isinstance(out_a, str) and out_a
