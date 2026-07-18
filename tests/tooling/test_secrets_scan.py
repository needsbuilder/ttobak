
from tooling.check_licenses import check_no_secrets


def test_clean_tree_has_no_secrets(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "core.py").write_text("def simplify(text: str) -> str:\n    return text\n", encoding="utf-8")
    assert check_no_secrets(tmp_path) == []


def test_aws_key_is_flagged(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "bad.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    violations = check_no_secrets(tmp_path)
    assert any(v.kind == "secret" for v in violations)
    assert any("aws-access-key" in v.detail for v in violations)


def test_anthropic_key_is_flagged(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "bad.py").write_text('TOKEN = "sk-ant-api03-' + "x" * 20 + '"\n', encoding="utf-8")
    assert any("anthropic-api-key" in v.detail for v in check_no_secrets(tmp_path))


def test_private_key_block_is_flagged(tmp_path):
    (tmp_path / "ttobak").mkdir()
    (tmp_path / "ttobak" / "key.pem").write_text("-----BEGIN RSA PRIVATE KEY-----\nMIIE\n", encoding="utf-8")
    assert any("private-key" in v.detail for v in check_no_secrets(tmp_path))


def test_korean_rrn_in_corpus_is_flagged(tmp_path):
    (tmp_path / "corpus").mkdir()
    (tmp_path / "corpus" / "pairs.jsonl").write_text('{"source_text": "신청자 주민등록번호 900101-1234567 확인"}\n', encoding="utf-8")
    violations = check_no_secrets(tmp_path)
    assert any(v.kind == "pii" for v in violations)
    assert any("korean-rrn" in v.detail for v in violations)


def test_test_fixtures_are_excluded(tmp_path):
    fix = tmp_path / "tests" / "tooling" / "fixtures"
    fix.mkdir(parents=True)
    (fix / "planted.py").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    assert check_no_secrets(tmp_path) == []


# Fix (CONFIRMED) — docs/ must not be blanket-excluded: a real secret planted
# anywhere under docs/ (other than the pinpointed known-fixture doc) must be
# caught, not silently skipped by a directory-wide exclusion.
def test_secret_directly_under_docs_is_flagged(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "notes.md").write_text('KEY = "AKIAIOSFODNN7EXAMPLE"\n', encoding="utf-8")
    violations = check_no_secrets(tmp_path)
    assert any("aws-access-key" in v.detail for v in violations)
