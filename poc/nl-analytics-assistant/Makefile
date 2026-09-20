# NL Analytics Assistant - developer convenience targets.
.PHONY: help setup data demo demo-gemini demo-ollama test lint cov qa qa-e2e \
        qa-live-ollama docker-build clean

PY ?= python3
VENV := .venv
BIN := $(VENV)/bin

help:
	@echo "make setup          - create venv and install dev deps"
	@echo "make data           - (re)generate synthetic demo data"
	@echo "make demo           - run the app locally (mock LLM + DuckDB) on :8080"
	@echo "make demo-gemini    - run with real Gemini via a free AI Studio key (NLA_GEMINI_API_KEY)"
	@echo "make demo-ollama    - run fully offline with a local Ollama model (NLA_OLLAMA_MODEL)"
	@echo "make test           - run the unit/integration test suite"
	@echo "make lint           - ruff static analysis"
	@echo "make cov            - test suite with coverage report"
	@echo "make qa             - lint + coverage (the full offline QA gate)"
	@echo "make qa-e2e         - browser end-to-end tests (needs a Chromium; NLA_E2E)"
	@echo "make qa-live-ollama - run the live Ollama integration test (needs Ollama running)"
	@echo "make docker-build   - build the Cloud Run container image"

setup:
	$(PY) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip
	$(BIN)/pip install -r app/requirements-dev.txt

data:
	$(BIN)/python data/generate_synthetic.py

demo:
	NLA_PROVIDER=mock NLA_EXECUTOR=duckdb \
		PYTHONPATH=app $(BIN)/uvicorn nl_analytics.main:app --host 0.0.0.0 --port 8080

# Real NL->SQL locally with a free Google AI Studio key (no GCP project).
# Get a key at https://aistudio.google.com/apikey then:
#   export NLA_GEMINI_API_KEY=...
demo-gemini:
	NLA_PROVIDER=aistudio NLA_EXECUTOR=duckdb \
		PYTHONPATH=app $(BIN)/uvicorn nl_analytics.main:app --host 0.0.0.0 --port 8080

# Real NL->SQL fully offline via a local Ollama server (no key, no internet).
# Pull a model first, e.g. `ollama pull qwen2.5-coder`, then:
#   export NLA_OLLAMA_MODEL=qwen2.5-coder
demo-ollama:
	NLA_PROVIDER=ollama NLA_EXECUTOR=duckdb \
		PYTHONPATH=app $(BIN)/uvicorn nl_analytics.main:app --host 0.0.0.0 --port 8080

test:
	$(BIN)/pytest -q

lint:
	$(BIN)/ruff check app data

cov:
	$(BIN)/pytest -q --cov=nl_analytics --cov-report=term-missing

# The full offline QA gate: everything that needs no cloud and no browser.
qa: lint cov

# Browser end-to-end (needs Chromium). On a fresh machine first run:
#   .venv/bin/playwright install chromium
qa-e2e:
	NLA_E2E=1 $(BIN)/pytest -q app/tests/e2e

# Live Ollama integration test (needs a running Ollama with a pulled model).
#   export NLA_OLLAMA_MODEL=qwen2.5-coder
qa-live-ollama:
	NLA_LIVE_OLLAMA=1 $(BIN)/pytest -q app/tests/live

docker-build:
	docker build -t nl-analytics-assistant:local .

clean:
	rm -rf $(VENV) .pytest_cache app/**/__pycache__
