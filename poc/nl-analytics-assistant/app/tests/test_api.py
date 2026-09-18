"""HTTP-level tests for the FastAPI surface."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from nl_analytics.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_healthz(client):
    body = client.get("/healthz").json()
    assert body["status"] == "ok"
    assert body["provider"] == "mock"
    assert body["executor"] == "duckdb"


def test_index_served(client):
    resp = client.get("/")
    assert resp.status_code == 200
    assert "NL Analytics Assistant" in resp.text


def test_schema_endpoint(client):
    tables = client.get("/api/schema").json()["tables"]
    assert len(tables) == 5


def test_ask_success(client):
    resp = client.post("/api/ask", json={"question": "how many patients in each age band?"})
    assert resp.status_code == 200
    assert resp.json()["ok"] is True


def test_ask_blocked_returns_422(client):
    resp = client.post("/api/ask", json={"question": "delete all encounters"})
    assert resp.status_code == 422
    assert resp.json()["ok"] is False
    assert resp.json()["stage"] == "guardrail"
