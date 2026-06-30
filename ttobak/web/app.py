"""또박 웹 데모 — Gradio 얇은 래퍼.

입력(텍스트 붙여넣기 또는 PDF/HWPX 업로드) + 등급 선택 -> parse() + simplify()
-> render_html() 나란히 + K-ER 점수 + Fidelity 배지 + 면책. 코어 API 재사용.
"""
from __future__ import annotations

import html as _html
from pathlib import Path

from ttobak.common import Verdict
from ttobak.levels import Level
from ttobak.metric.models import KERReport
from ttobak.parse import parse
from ttobak.pipeline import simplify
from ttobak.providers.base import LLMProvider
from ttobak.render import render_html

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


_FIDELITY_LABEL: dict[Verdict, str] = {
    Verdict.PASS: "Fidelity 통과 ✅",
    Verdict.REVISE: "Fidelity 재교정됨 🔁",
    Verdict.HUMAN_REVIEW: "검수 필요 ⚠️ (사람 확인 권장)",
}


def _ker_badge(ker: KERReport) -> str:
    """K-ER 점수 한 줄 요약. '규칙 기반·미검증 보조 지표'임을 명시한다."""
    n = len(ker.violations)
    return f"K-ER {ker.score:.0f}/100 · 위반 {n}건 (규칙 기반 루브릭, 경험적 검증 아님)"


def _fidelity_badge(verdict: Verdict) -> str:
    """Fidelity 판정 배지 텍스트."""
    return _FIDELITY_LABEL.get(verdict, "검수 필요 ⚠️")


_DISCLAIMER = (
    "쉬운본은 자동 변환된 보조 자료이며, 법적 효력은 원문이 우선합니다. "
    "숫자·날짜·금액·기한은 반드시 원문으로 다시 확인하세요."
)

_INTRO = (
    "# 또박 (Ttobak) — 쉬운 정보 변환 데모\n"
    "어려운 공공·행정 문서를 쉬운 글로 바꾸고, 쉬움(K-ER)과 "
    "사실충실성(Fidelity)을 함께 측정합니다."
)


def build_app(provider: "LLMProvider | None" = None) -> "gr.Blocks":
    """Gradio 데모를 구성해 Blocks 를 반환한다(launch 는 호출자 책임)."""
    import gradio as gr

    from ttobak.web.provider import make_provider

    bound_provider = provider if provider is not None else make_provider()

    def _on_click(text_input: str, file_obj, level_label: str):
        return simplify_handler(text_input, file_obj, level_label, bound_provider)

    with gr.Blocks(title="또박 Ttobak", analytics_enabled=False) as demo:
        gr.Markdown(_INTRO)
        with gr.Row():
            with gr.Column(scale=1):
                with gr.Tab("텍스트 붙여넣기"):
                    text_input = gr.Textbox(label="원문 텍스트", lines=10,
                                            placeholder="여기에 공문·고지서·안내문 내용을 붙여넣으세요.")
                with gr.Tab("파일 업로드 (PDF·HWPX)"):
                    file_input = gr.File(label="문서 업로드", file_types=[".pdf", ".hwpx", ".hwp", ".txt"])
                level_input = gr.Radio(choices=list(LEVEL_CHOICES.keys()),
                                       value=next(iter(LEVEL_CHOICES)), label="출력 등급")
                run_btn = gr.Button("변환", variant="primary")
                ker_out = gr.Label(label="K-ER (쉬움 지표 · 규칙 기반·미검증)")
                fid_out = gr.Label(label="Fidelity (사실충실성 게이트)")
            with gr.Column(scale=2):
                html_out = gr.HTML(label="결과 (원문 · 쉬운본 나란히)")
        gr.Markdown(f"> ⚖️ **면책**: {_DISCLAIMER}")

        run_btn.click(fn=_on_click, inputs=[text_input, file_input, level_input],
                      outputs=[html_out, ker_out, fid_out])
    return demo


def simplify_handler(text_input: str, file_obj, level_label: str, provider: LLMProvider) -> tuple[str, str, str]:
    """Gradio 버튼 핸들러 — (html, ker_badge, fidelity_badge) 반환.

    예외는 절대 올리지 않는다(UI가 500 대신 메시지를 보여주도록):
    실패 시 슬롯 0에 오류 HTML, 배지는 빈 문자열.
    """
    try:
        source, mime = _load_source(text_input, file_obj)
        level = _resolve_level(level_label)
        doc = parse(source, mime)
        result = simplify(doc, level, provider)
        html = render_html(result)
        return html, _ker_badge(result.ker), _fidelity_badge(result.fidelity.verdict)
    except Exception as exc:  # noqa: BLE001 — 데모 UI는 어떤 실패도 메시지로 표시
        msg = _html.escape(str(exc)) or "변환 중 오류가 발생했습니다."
        return f'<div class="ttobak-error">변환 오류: {msg}</div>', "", ""
