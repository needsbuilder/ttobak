from pathlib import Path

from ttobak.eval.corpus import validate_corpus

CORPUS = Path(__file__).resolve().parents[2] / "corpus"


def test_required_files_exist():
    for name in ("pairs.jsonl", "DATA_LICENSE", "SOURCES.csv", "NOTICE-sources.md", "DATASET_CARD.md"):
        assert (CORPUS / name).is_file(), f"missing corpus/{name}"


def test_data_license_is_cc_by_40():
    text = (CORPUS / "DATA_LICENSE").read_text(encoding="utf-8")
    assert "CC BY 4.0" in text or "Creative Commons Attribution 4.0" in text


def test_dataset_card_states_ship_target_and_roadmap():
    text = (CORPUS / "DATASET_CARD.md").read_text(encoding="utf-8")
    assert "8" in text and "12" in text
    assert "100" in text and "300" in text
    assert "합성" in text or "synthetic" in text.lower()
    assert "원문" in text


def test_notice_has_kogl1_attribution_template():
    text = (CORPUS / "NOTICE-sources.md").read_text(encoding="utf-8")
    assert "공공누리" in text and "제1유형" in text


def test_sources_csv_header():
    header = (CORPUS / "SOURCES.csv").read_text(encoding="utf-8").splitlines()[0]
    for col in ("title", "agency", "year", "url", "kogl_type", "date_fetched"):
        assert col in header


def test_shipped_pairs_jsonl_validates_against_schema():
    pairs = validate_corpus(CORPUS / "pairs.jsonl")
    assert len(pairs) >= 1
    assert pairs[0].source_text and pairs[0].easy_text
    assert pairs[0].fidelity_checks.deadlines in (True, False)
