# Targets from build.md Section 5. Targets for later phases print a notice until implemented.
# On Windows the venv interpreter lives in .venv/Scripts; elsewhere in .venv/bin.
ifeq ($(OS),Windows_NT)
PY ?= .venv/Scripts/python
else
PY ?= .venv/bin/python
endif

.PHONY: setup lint test data-check env midair-eval auair-prep auair-eval visdrone-prep \
        train track-eval export bench demo docs all-results

setup:
	python -m venv .venv
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-lock.txt
	$(PY) -m pip install -e . --no-deps

lint:
	$(PY) -m ruff check src tests scripts
	$(PY) -m ruff format --check src tests scripts

test:
	$(PY) -m pytest --cov=aerialrange --cov-report=term-missing

data-check:
	$(PY) scripts/check_data.py

env:
	$(PY) scripts/env_report.py

midair-eval auair-prep auair-eval visdrone-prep train track-eval export bench demo docs all-results:
	@echo "'$@' is not implemented yet (later phase; see build.md Section 12)." && exit 1
