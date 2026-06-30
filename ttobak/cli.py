"""`ttobak` 콘솔 명령. 서브커맨드: `web` (데모 서버). M11이 `audit` 를 추가한다."""
from __future__ import annotations

import argparse


def _serve(host: str, port: int, provider_name: str | None, share: bool) -> None:
    """앱을 빌드해 Gradio 서버를 띄운다(테스트에서 패치 가능하도록 분리)."""
    from ttobak.web.app import build_app
    from ttobak.web.provider import make_provider

    demo = build_app(provider=make_provider(provider_name))
    demo.launch(server_name=host, server_port=port, share=share)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="ttobak", description="또박 — 한국어 쉬운 정보 엔진")
    sub = parser.add_subparsers(dest="command")

    web = sub.add_parser("web", help="Gradio 웹 데모 실행")
    web.add_argument("--host", default="127.0.0.1", help="바인드 호스트 (기본 127.0.0.1)")
    web.add_argument("--port", type=int, default=7860, help="포트 (기본 7860)")
    web.add_argument("--provider", default=None,
                     help="LLM 프로바이더 이름 (anthropic|fake). 미지정 시 $TTOBAK_PROVIDER 또는 anthropic")
    web.add_argument("--share", action="store_true", help="Gradio 공개 링크 생성")

    audit_p = sub.add_parser("audit", help="라이선스·보안 게이트 실행 (spec 14.5)")
    audit_p.add_argument("--root", default=".", help="스캔할 레포 루트 (기본: 현재 디렉터리)")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)

    if args.command == "web":
        _serve(args.host, args.port, args.provider, args.share)
        return 0

    if args.command == "audit":
        from tooling import check_licenses
        return check_licenses.main(["--root", args.root])

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
