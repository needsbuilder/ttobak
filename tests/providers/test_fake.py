import pytest

from ttobak.providers.base import LLMProvider
from ttobak.providers.fake import FakeProvider


def test_fakeprovider_satisfies_protocol():
    assert isinstance(FakeProvider(["x"]), LLMProvider)


def test_returns_scripted_responses_in_fifo_order():
    fake = FakeProvider(["첫 번째 쉬운 글입니다.", "두 번째 응답입니다."])
    assert fake.generate("원문1") == "첫 번째 쉬운 글입니다."
    assert fake.generate("원문2") == "두 번째 응답입니다."


def test_records_each_call_with_args():
    fake = FakeProvider(["응답"])
    fake.generate("쉬운 글로 바꿔주세요", system="너는 쉬운 글 변환기다", max_tokens=512)
    assert fake.calls == [
        {
            "prompt": "쉬운 글로 바꿔주세요",
            "system": "너는 쉬운 글 변환기다",
            "max_tokens": 512,
        }
    ]


def test_falls_back_to_default_when_queue_empty():
    fake = FakeProvider(["하나만 있음"], default="기본 응답")
    assert fake.generate("a") == "하나만 있음"
    assert fake.generate("b") == "기본 응답"
    assert fake.generate("c") == "기본 응답"


def test_raises_when_queue_empty_and_no_default():
    fake = FakeProvider(["하나만 있음"])
    fake.generate("a")
    with pytest.raises(IndexError, match="FakeProvider"):
        fake.generate("b")


def test_empty_construction_uses_default_only():
    fake = FakeProvider(default="항상 같은 응답")
    assert fake.generate("a") == "항상 같은 응답"
    assert fake.generate("b") == "항상 같은 응답"
