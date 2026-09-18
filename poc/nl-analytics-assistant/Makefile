# NL Analytics Assistant - developer convenience targets.
.PHONY: help setup data demo test docker-build clean

PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

help:
	@echo "make setup        - create venv and install dev deps"
	@echo "make data         - (re)generate synthetic demo data"
	@echo "make demo         - run the app locally (mock LLM + DuckDB) on :8080"
	@echo "make test         - run the test suite"
	@echo "make docker-build - build the Cloud Run container image"

setup:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r app/requirements-dev.txt

data:
	$(BIN)/python data/generate_synthetic.py

demo:
	NLA_PROVIDER=mock NLA_EXECUTOR=duckdb \
		PYTHONPATH=app $(BIN)/uvicorn nl_analytics.main:app --host 0.0.0.0 --port 8080

test:
	PYTHONPATH=app $(BIN)/pytest -q app/tests

docker-build:
	docker build -t nl-analytics-assistant:local .

clean:
	rm -rf $(VENV) .pytest_cache app/**/__pycache__
