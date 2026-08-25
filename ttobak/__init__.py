"""또박(Ttobak) — open-source Korean Easy-Read engine.

Turns hard Korean public/administrative documents into easy-read text,
measures easiness (K-ER score), self-corrects, and preserves facts via a
fidelity gate. Apache-2.0.
"""

__version__ = "0.2.0"

# 공개 API 재export — 다른 프로젝트가 코어를 가져다 쓸 때 서브모듈 경로를 몰라도 되게 한다.
# 정본은 각 서브모듈이며 여기서는 이름만 다시 노출한다. pipeline 이 테스트 monkeypatch 를
# 위해 score/verify 를 모듈 레벨로 들고 있는 구조는 건드리지 않는다.
#
# parse 는 일부러 빠져 있다: `ttobak.parse` 는 서브패키지 이름이기도 해서 최상위 이름을
# 함수로 덮으면 `import ttobak.parse.pdf_parser` 가 깨진다. 하나의 이름이 모듈이면서
# 함수일 수는 없다. parse 는 `from ttobak.parse import parse` 가 정본이다.
from ttobak.fidelity import verify
from ttobak.metric import score
from ttobak.pictogram import match
from ttobak.pipeline import simplify
from ttobak.render import render_html

__all__ = [
    "simplify",
    "score",
    "verify",
    "match",
    "render_html",
    "__version__",
]
