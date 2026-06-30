import inspect

from ttobak.providers.base import LLMProvider


def test_llmprovider_is_runtime_checkable_protocol():
    # A conforming class must satisfy isinstance against the Protocol.
    class Conforming:
        def generate(self, prompt: str, *, system: str | None = None, max_tokens: int = 2048) -> str:
            return "ok"

    assert isinstance(Conforming(), LLMProvider)


def test_non_conforming_class_is_not_instance():
    class Missing:
        def something_else(self) -> str:
            return "no"

    assert not isinstance(Missing(), LLMProvider)


def test_generate_signature_matches_contract():
    sig = inspect.signature(LLMProvider.generate)
    params = sig.parameters
    assert list(params) == ["self", "prompt", "system", "max_tokens"]
    assert params["system"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["max_tokens"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["max_tokens"].default == 2048
    assert params["system"].default is None
