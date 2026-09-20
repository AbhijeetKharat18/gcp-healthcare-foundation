"""Live integration test against a real Ollama server.

Opt-in and environment-gated so it never runs in CI or the default suite:
requires NLA_LIVE_OLLAMA=1 AND a reachable Ollama server. Run it on the machine
where Ollama is installed:

    export NLA_OLLAMA_MODEL=qwen2.5-coder   # a model you've pulled
    make qa-live-ollama

It exercises the *real* model end-to-end: NL question -> Ollama -> guardrails ->
DuckDB over synthetic data. Local models vary in quality, so it passes if at
least one of several simple questions returns rows, and it asserts the pipeline
and guardrails hold for every attempt (any generated SQL touches only
secure_views).
"""

from __future__ import annotations

import os
import urllib.request

import pytest
from nl_analytics.config import load_settings
from nl_analytics.executor.duckdb_exec import DuckDBExecutor
from nl_analytics.llm.ollama import OllamaProvider
from nl_analytics.service import AnalyticsService

pytestmark = pytest.mark.live_ollama

_HOST = os.getenv("NLA_OLLAMA_HOST", "http://localhost:11434")
_MODEL = os.getenv("NLA_OLLAMA_MODEL", "llama3.1")

QUESTIONS = [
    "How many patients are in each age band?",
    "What is the average length of stay by encounter type?",
    "How many encounters are there per facility?",
]

ALLOWED = {
    "v_facility_dim", "v_patient_summary", "v_encounter_facts",
    "v_condition_facts", "v_observation_facts",
}


def _reachable() -> bool:
    try:
        with urllib.request.urlopen(f"{_HOST}/api/tags", timeout=2) as resp:
            return resp.status == 200
    except Exception:
        return False


@pytest.fixture(scope="module")
def service() -> AnalyticsService:
    if os.getenv("NLA_LIVE_OLLAMA") != "1":
        pytest.skip("set NLA_LIVE_OLLAMA=1 to run the live Ollama test")
    if not _reachable():
        pytest.skip(f"Ollama not reachable at {_HOST}")
    return AnalyticsService(
        provider=OllamaProvider(host=_HOST, model=_MODEL),
        executor=DuckDBExecutor(load_settings().data_dir),
    )


def test_real_model_answers_at_least_one(service):
    successes = 0
    for q in QUESTIONS:
        r = service.ask(q)
        # Whatever the model produced, the guardrails must have held: any
        # executed SQL touches only secure_views tables.
        for table in r.tables_used:
            assert table in ALLOWED
        if r.ok and r.row_count > 0:
            successes += 1
    assert successes >= 1, "the local model produced no usable query for any question"
