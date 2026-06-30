from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

SHIPPED_DEPS = [
    "hwp-hwpx-parser", "olefile", "python-docx", "pypdf", "pdfminer.six",
    "kiwipiepy", "dateparser", "korean-number", "es-hangul",
    "kf-deberta-base-cross-nli", "bert-score", "sentence-transformers",
    "transformers", "spaCy", "ko_core_news_lg", "fastapi", "uvicorn",
    "pydantic", "mcp", "Ollama", "Qwen2.5", "Kanana", "Mulberry", "OpenMoji",
]
FORBIDDEN_MENTIONS = ["pyhwp", "KoNLPy", "EXAONE", "ARASAAC"]


def test_third_party_licenses_covers_every_shipped_dep():
    text = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8").lower()
    missing = [dep for dep in SHIPPED_DEPS if dep.lower() not in text]
    assert missing == [], f"undocumented deps: {missing}"


def test_notice_has_required_verbatim_attributions():
    text = (ROOT / "NOTICE").read_text(encoding="utf-8")
    assert "Apache License" in text or "Apache-2.0" in text
    assert "Built with Qwen" in text
    assert "OpenMoji" in text and "CC BY-SA 4.0" in text
    assert "Mulberry" in text and "CC BY-SA 2.0 UK" in text
    assert "LGPL" in text


def test_forbidden_components_only_appear_as_excluded():
    text = (ROOT / "THIRD_PARTY_LICENSES.md").read_text(encoding="utf-8")
    for name in FORBIDDEN_MENTIONS:
        hit_lines = [ln for ln in text.splitlines() if name.lower() in ln.lower()]
        assert hit_lines, f"{name} must be documented as excluded"
        assert all(
            any(k in ln.lower() for k in ("excluded", "non-commercial", "avoided", "not shipped", "blocker"))
            for ln in hit_lines), f"{name} mentioned without exclusion marker"
