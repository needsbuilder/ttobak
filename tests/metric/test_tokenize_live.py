"""kiwipiepy 실통합 스모크 — 핀 범위의 실제 버전에서 tokenize()가 작동함을 검증.

단위 테스트는 주입된 Token 리스트로 도니(결정론), 핀을 넓히거나 올릴 때
실제 kiwipiepy API와의 계약(form/tag 속성, Kiwi().tokenize)이 깨지지 않았는지는
이 스모크만이 검증한다. kiwipiepy 미설치 환경(선택 의존성 없는 개발 셋업)에서는
건너뛴다 — CI는 core deps로 kiwipiepy를 설치하므로 항상 실행된다.
"""
import pytest

pytest.importorskip("kiwipiepy")

from ttobak.metric.tokenize import Token, tokenize


def test_live_tokenize_returns_form_tag_tokens():
    tokens = tokenize("만 65세 이상 어르신은 강서구청에 신청하세요.")
    assert tokens, "live tokenizer returned nothing"
    assert all(isinstance(t, Token) and t.form and t.tag for t in tokens)
    # 형태소 분리의 최소 계약: 숫자와 명사가 각자 토큰으로 나온다.
    forms = [t.form for t in tokens]
    assert "65" in forms
    assert any("구청" in f for f in forms)
