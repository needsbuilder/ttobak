from pdfminer.high_level import extract_text
from pypdf import PdfReader
import io

from ttobak.parse._fixtures import make_minimal_pdf, make_minimal_hwpx


def test_make_minimal_pdf_is_readable_by_pypdf():
    data = make_minimal_pdf(["Hello Ttobak", "Line two"])
    assert isinstance(data, bytes)
    assert data.startswith(b"%PDF-")
    reader = PdfReader(io.BytesIO(data))
    assert len(reader.pages) == 1
    text = reader.pages[0].extract_text()
    assert "Hello Ttobak" in text
    assert "Line two" in text


def test_make_minimal_pdf_is_readable_by_pdfminer():
    data = make_minimal_pdf(["Fallback path"])
    text = extract_text(io.BytesIO(data))
    assert "Fallback path" in text


def test_make_minimal_hwpx_is_a_zip_owpml():
    data = make_minimal_hwpx(["문단 하나", "문단 둘"])
    assert isinstance(data, bytes)
    assert data[:2] == b"PK"
    import zipfile, io as _io
    zf = zipfile.ZipFile(_io.BytesIO(data))
    names = zf.namelist()
    assert "mimetype" in names
    assert any(n.startswith("Contents/section") for n in names)
