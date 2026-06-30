"""Deterministic, dependency-free fixture builders for parser tests.

``make_minimal_pdf`` hand-writes a minimal but spec-valid single-page PDF using
Helvetica so both pypdf and pdfminer.six can extract its text. ``make_minimal_hwpx``
builds a minimal OWPML ZIP that hwp-hwpx-parser's Reader can open. Raw bytes only.
"""
from __future__ import annotations

import io
import zipfile


def _pdf_escape(text: str) -> str:
    return text.replace("\\", r"\\").replace("(", r"\(").replace(")", r"\)")


def make_minimal_pdf(lines: list[str]) -> bytes:
    """Return a valid single-page PDF showing each string in ``lines`` (Helvetica 12pt, ASCII)."""
    content_parts = ["BT", "/F1 12 Tf", "72 720 Td", "16 TL"]
    for i, line in enumerate(lines):
        if i > 0:
            content_parts.append("T*")
        content_parts.append(f"({_pdf_escape(line)}) Tj")
    content_parts.append("ET")
    content = ("\n".join(content_parts)).encode("latin-1")

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>"
    )
    objects.append(
        b"<< /Length " + str(len(content)).encode("latin-1") + b" >>\nstream\n" + content + b"\nendstream"
    )
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets: list[int] = []
    for idx, body in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(str(idx).encode("latin-1") + b" 0 obj\n")
        out.write(body)
        out.write(b"\nendobj\n")

    xref_pos = out.tell()
    n = len(objects) + 1
    out.write(b"xref\n")
    out.write(b"0 " + str(n).encode("latin-1") + b"\n")
    out.write(b"0000000000 65535 f \n")
    for off in offsets:
        out.write(f"{off:010d} 00000 n \n".encode("latin-1"))
    out.write(b"trailer\n")
    out.write(b"<< /Size " + str(n).encode("latin-1") + b" /Root 1 0 R >>\n")
    out.write(b"startxref\n")
    out.write(str(xref_pos).encode("latin-1") + b"\n")
    out.write(b"%%EOF")
    return out.getvalue()


_HWPX_VERSION_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<hv:HCFVersion xmlns:hv="http://www.hancom.co.kr/hwpml/2011/version" '
    'tagetApplication="WORDPROCESSOR" major="5" minor="0" micro="5" '
    'buildNumber="0" os="1" xmlVersion="1.4" application="Hancom Office" '
    'appVersion="11.0.0.0"/>'
)

_HWPX_CONTENT_HPF = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<opf:package xmlns:opf="http://www.idpf.org/2007/opf/" '
    'version="" unique-identifier="" id="">'
    '<opf:spine><opf:itemref idref="section0"/></opf:spine>'
    '</opf:package>'
)

_HWPX_HEADER = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<hh:head xmlns:hh="http://www.hancom.co.kr/hwpml/2011/head" '
    'version="1.4" secCnt="1"></hh:head>'
)


def _hwpx_section(paragraphs: list[str]) -> str:
    ns = (
        'xmlns:hs="http://www.hancom.co.kr/hwpml/2011/section" '
        'xmlns:hp="http://www.hancom.co.kr/hwpml/2011/paragraph"'
    )
    body = []
    for text in paragraphs:
        escaped = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        body.append('<hp:p><hp:run><hp:t>' + escaped + '</hp:t></hp:run></hp:p>')
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<hs:sec ' + ns + '>' + "".join(body) + '</hs:sec>'
    )


def make_minimal_hwpx(paragraphs: list[str]) -> bytes:
    """Return a minimal valid HWPX (OWPML ZIP) containing ``paragraphs``."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be first and stored uncompressed per OCF.
        zf.writestr(zipfile.ZipInfo("mimetype"), "application/hwp+zip", compress_type=zipfile.ZIP_STORED)
        zf.writestr("version.xml", _HWPX_VERSION_XML)
        zf.writestr("Contents/content.hpf", _HWPX_CONTENT_HPF)
        zf.writestr("Contents/header.xml", _HWPX_HEADER)
        zf.writestr("Contents/section0.xml", _hwpx_section(paragraphs))
    return buf.getvalue()
