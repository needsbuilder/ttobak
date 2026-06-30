from __future__ import annotations

from datetime import date

import pytest

from ttobak.ir import Block, BlockType, Document
from ttobak.providers.fake import FakeProvider


@pytest.fixture
def fake_provider() -> FakeProvider:
    # default-backed so generate() is total and deterministic
    return FakeProvider(default="쉬운 글로 바꾼 결과입니다.")


@pytest.fixture
def ref_date() -> date:
    return date(2026, 7, 1)


@pytest.fixture
def sample_document() -> Document:
    return Document(
        source_mime="text/plain",
        blocks=[
            Block(type=BlockType.HEADING, text="건강보험료 납부 안내", level=1),
            Block(type=BlockType.PARAGRAPH, text="이번 달 납부하실 건강보험료는 1,295,400원입니다."),
            Block(type=BlockType.PARAGRAPH, text="납부 기한은 2026년 7월 17일까지입니다."),
            Block(type=BlockType.LIST_ITEM, text="만 65세 이상은 경감 대상에서 제외됩니다."),
        ],
    )
