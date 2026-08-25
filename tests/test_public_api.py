"""공개 API 표면 — README·결과보고서가 소개하는 함수들을 실제로 쓸 수 있어야 한다.

문서는 parse·simplify·score·verify·match·render_html 을 공개 API 로 소개하는데,
그동안 패키지 최상위에는 아무것도 없어서(`from ttobak import simplify` 는 ImportError)
서브모듈 경로를 아는 사람만 쓸 수 있었다.

`parse` 만 예외다: `ttobak.parse` 는 서브패키지 이름이기도 해서, 최상위 이름을 함수로
덮으면 `import ttobak.parse.pdf_parser` 가 깨진다(하나의 이름이 모듈이면서 함수일 수는
없다). 그래서 parse 는 모듈 경로를 정본으로 유지한다. 서브패키지 리네임은 파괴적 변경
이라 별도 결정 사항이다.
"""
import importlib

import ttobak

ROOT_EXPORTS = ["simplify", "score", "verify", "match", "render_html"]


def test_root_exports_are_importable():
    missing = [name for name in ROOT_EXPORTS if not hasattr(ttobak, name)]
    assert not missing, f"패키지 최상위에서 빠진 공개 함수: {missing}"


def test_root_exports_are_the_canonical_implementations():
    """재export 가 사본이 아니라 정본을 가리켜야 한다 (monkeypatch 계약 보존)."""
    from ttobak.fidelity import verify
    from ttobak.metric import score
    from ttobak.pictogram import match
    from ttobak.pipeline import simplify
    from ttobak.render import render_html

    assert ttobak.simplify is simplify
    assert ttobak.score is score
    assert ttobak.verify is verify
    assert ttobak.match is match
    assert ttobak.render_html is render_html


def test_all_declares_the_root_surface():
    for name in ROOT_EXPORTS:
        assert name in ttobak.__all__, f"__all__ 에 {name} 없음"


def test_parse_stays_a_traversable_subpackage():
    """parse 는 이름 충돌 때문에 최상위로 올리지 않는다. 모듈 경로가 정본이다."""
    from ttobak.parse import parse

    assert callable(parse)
    # 최상위 이름을 함수로 덮었다면 이 줄이 ImportError 로 죽는다.
    assert importlib.import_module("ttobak.parse.pdf_parser") is not None
    assert "parse" not in ttobak.__all__
