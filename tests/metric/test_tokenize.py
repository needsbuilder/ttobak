from ttobak.metric.tokenize import Token, split_sentences, tokenize


def test_token_dataclass_fields():
    t = Token(form="보험료", tag="NNG")
    assert t.form == "보험료"
    assert t.tag == "NNG"


def test_split_sentences_splits_on_terminal_punctuation():
    text = "보험료를 내세요. 기한은 7월 17일입니다! 문의 주세요?"
    sents = split_sentences(text)
    assert len(sents) == 3
    assert sents[0].strip() == "보험료를 내세요."


def test_tokenize_returns_tokens_with_form_and_tag():
    tokens = tokenize("보험료를 납부하세요.")
    assert tokens, "tokenize must return at least one token"
    assert all(isinstance(t, Token) for t in tokens)
    assert all(isinstance(t.form, str) and isinstance(t.tag, str) for t in tokens)
