"""Edge-case and negative input handling (API validation + guardrails)."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from nl_analytics.guardrails import GuardrailError, enforce
from nl_analytics.main import app
from nl_analytics.service import AnalyticsService


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


@pytest.fixture(scope="module")
def service() -> AnalyticsService:
    return AnalyticsService()


def test_api_rejects_oversized_question(client):
    # pydantic max_length=500 -> 422 validation error before it reaches the model.
    resp = client.post("/api/ask", json={"question": "x" * 501})
    assert resp.status_code == 422


def test_api_rejects_missing_field(client):
    resp = client.post("/api/ask", json={})
    assert resp.status_code == 422


def test_api_rejects_empty_string(client):
    # min_length=1 -> validation error.
    resp = client.post("/api/ask", json={"question": ""})
    assert resp.status_code == 422


def test_unicode_question_is_handled(service):
    # Non-ASCII input must not crash; mock falls back to a safe query.
    r = service.ask("readmission rate by facility — éàü \U0001f3e5")
    assert r.ok
    assert r.row_count >= 0


def test_whitespace_question_rejected_by_service(service):
    r = service.ask("     ")
    assert not r.ok
    assert r.stage == "generate"


def test_comment_based_injection_blocked():
    # A trailing statement hidden after an inline comment is still two
    # statements -> blocked.
    sql = (
        "SELECT * FROM secure_views.v_facility_dim -- harmless\n"
        "; DROP TABLE secure_views.v_facility_dim"
    )
    with pytest.raises(GuardrailError):
        enforce(sql)


def test_block_comment_injection_blocked():
    sql = "SELECT * FROM secure_views.v_facility_dim /* ; DELETE */ ; DELETE FROM secure_views.v_facility_dim"
    with pytest.raises(GuardrailError):
        enforce(sql)
