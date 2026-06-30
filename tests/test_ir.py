import pytest
from pydantic import ValidationError

from ttobak.ir import Block, BlockType, Document


def test_blocktype_values():
    assert BlockType.HEADING == "heading"
    assert BlockType.PARAGRAPH == "paragraph"
    assert BlockType.LIST_ITEM == "list_item"
    assert BlockType.TABLE == "table"
    assert BlockType.CAPTION == "caption"


def test_block_defaults():
    b = Block(type=BlockType.PARAGRAPH)
    assert b.text == ""
    assert b.level == 0
    assert b.cells is None
    assert b.bbox is None
    assert b.confidence == 1.0


def test_block_full_construction():
    b = Block(
        type=BlockType.TABLE,
        text="요약",
        level=2,
        cells=[["항목", "금액"], ["보험료", "1,295,400원"]],
        bbox=(0.0, 0.0, 100.0, 50.0),
        confidence=0.8,
    )
    assert b.type == BlockType.TABLE
    assert b.cells[1][1] == "1,295,400원"
    assert b.bbox == (0.0, 0.0, 100.0, 50.0)
    assert b.confidence == 0.8


def test_block_type_is_required():
    with pytest.raises(ValidationError):
        Block()


def test_document_text_joins_block_text_with_newlines():
    doc = Document(
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="2026년 7월분 보험료를 안내드립니다."),
            Block(type=BlockType.LIST_ITEM, text="납부 기한: 2026년 7월 25일"),
        ],
        source_mime="text/plain",
    )
    assert doc.text() == (
        "건강보험료 납부 안내\n"
        "2026년 7월분 보험료를 안내드립니다.\n"
        "납부 기한: 2026년 7월 25일"
    )


def test_document_meta_defaults_to_empty_dict():
    doc = Document(blocks=[], source_mime="text/plain")
    assert doc.meta == {}
    assert doc.text() == ""


def test_document_meta_is_per_instance():
    doc1 = Document(blocks=[], source_mime="text/plain")
    doc2 = Document(blocks=[], source_mime="text/plain")
    doc1.meta["key"] = "value"
    assert "key" not in doc2.meta
