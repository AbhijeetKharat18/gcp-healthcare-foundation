"""Settings are read from the environment at call time (not import time)."""

from __future__ import annotations

from nl_analytics.config import load_settings


def test_defaults_are_offline(monkeypatch):
    for var in ["NLA_PROVIDER", "NLA_EXECUTOR"]:
        monkeypatch.delenv(var, raising=False)
    s = load_settings()
    assert s.provider == "mock"
    assert s.executor == "duckdb"


def test_env_overrides_are_picked_up(monkeypatch):
    monkeypatch.setenv("NLA_PROVIDER", "vertex")
    monkeypatch.setenv("NLA_EXECUTOR", "bigquery")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "hcf-dev-lakehouse")
    monkeypatch.setenv("NLA_MAX_ROWS", "50")
    s = load_settings()
    assert s.provider == "vertex"
    assert s.executor == "bigquery"
    assert s.gcp_project == "hcf-dev-lakehouse"
    # vertex_project falls back to GOOGLE_CLOUD_PROJECT when unset.
    assert s.vertex_project == "hcf-dev-lakehouse"
    assert s.max_rows == 50


def test_vertex_project_env_takes_precedence(monkeypatch):
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "hcf-dev-lakehouse")
    monkeypatch.setenv("NLA_VERTEX_PROJECT", "hcf-dev-delivery")
    s = load_settings()
    assert s.vertex_project == "hcf-dev-delivery"
