import pytest

from ttobak.parse._fixtures import make_minimal_pdf, make_minimal_hwpx


@pytest.fixture
def pdf_bytes() -> bytes:
    return make_minimal_pdf(["Ttobak PDF body", "Second visible line"])


@pytest.fixture
def hwpx_bytes() -> bytes:
    return make_minimal_hwpx(["청년 주거지원 안내문", "신청 기간은 정해져 있습니다."])
