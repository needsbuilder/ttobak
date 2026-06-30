.PHONY: audit test install-audit

install-audit:
	python -m pip install -e ".[audit]"

audit:
	python -m tooling.check_licenses --root .

test:
	python -m pytest -q
