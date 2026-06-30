"""또박 웹 데모 — Gradio 얇은 래퍼.

입력(텍스트 붙여넣기 또는 PDF/HWPX 업로드) + 등급 선택 -> parse() + simplify()
-> render_html() 나란히 + K-ER 점수 + Fidelity 배지 + 면책. 코어 API 재사용.
"""
from __future__ import annotations

from pathlib import Path

from ttobak.levels import Level

# 사람이 읽는 한국어 라벨 -> Level. 순서 보존(dict).
LEVEL_CHOICES: dict[str, Level] = {
    "쉬운 글 (Easy Korean, 문해수준 1–2)": Level.EASY,
    "보통 읽기 (Plain Language, 문해수준 3)": Level.PLAIN,
}

_EXT_TO_MIME: dict[str, str] = {
    ".pdf": "application/pdf",
    ".hwpx": "application/vnd.hancom.hwpx",
    ".hwp": "application/x-hwp",
    ".txt": "text/plain",
}


def _resolve_level(level_label: str) -> Level:
    """UI 라벨을 Level 로. 알 수 없으면 가장 쉬운 등급(EASY)으로 폴백한다."""
    return LEVEL_CHOICES.get(level_label, Level.EASY)


def _load_source(text_input: str, file_obj) -> tuple[bytes | str, str]:
    """UI 입력을 parse() 가 받는 (source, mime) 로 변환한다.

    파일이 있으면 파일 우선(바이트 + 확장자 기반 MIME), 없으면 붙여넣은 텍스트.
    둘 다 비어 있으면 ValueError.
    """
    path = _file_path(file_obj)
    if path is not None:
        data = Path(path).read_bytes()
        mime = _EXT_TO_MIME.get(Path(path).suffix.lower(), "text/plain")
        return data, mime

    text = (text_input or "").strip()
    if not text:
        raise ValueError("변환할 텍스트를 입력하거나 파일을 업로드해 주세요.")
    return text, "text/plain"


def _file_path(file_obj) -> str | None:
    """Gradio File 컴포넌트가 주는 값(경로 문자열 또는 .name 속성)에서 경로를 뽑는다."""
    if file_obj is None:
        return None
    if isinstance(file_obj, str):
        return file_obj
    name = getattr(file_obj, "name", None)
    return name if isinstance(name, str) else None
