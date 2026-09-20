"""Vertex provider logic tests with a faked google-genai client (no network).

The Vertex provider uses the google-genai SDK in Vertex mode; we inject a fake
client so we exercise the provider's own logic (prompt assembly, response
handling, clean_sql) without any cloud call.
"""

from __future__ import annotations

import pytest
from nl_analytics.llm import build_provider
from nl_analytics.llm.vertex import VertexGeminiProvider


class _FakeResp:
    def __init__(self, text):
        self._text = text

    @property
    def text(self):
        return self._text


class _FakeModels:
    def __init__(self, text):
        self._text = text
        self.last_kwargs = None

    def generate_content(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeResp(self._text)


class _FakeClient:
    def __init__(self, text):
        self.models = _FakeModels(text)


def _provider(text) -> VertexGeminiProvider:
    p = VertexGeminiProvider(project="p", location="us-central1", model="gemini-2.5-pro")
    p._client = _FakeClient(text)  # skip real genai.Client construction
    return p


def test_requires_project():
    with pytest.raises(ValueError, match="requires a project"):
        VertexGeminiProvider(project="", location="us-central1", model="m")


def test_generates_and_cleans_sql():
    p = _provider("```sql\nSELECT 1 FROM secure_views.v_facility_dim;\n```")
    assert p.generate_sql("q", "sys") == "SELECT 1 FROM secure_views.v_facility_dim"


def test_prompt_and_model_passed():
    p = _provider("SELECT 1")
    p.generate_sql("how many facilities?", "SYSTEM-RULES")
    kwargs = p._client.models.last_kwargs
    assert kwargs["model"] == "gemini-2.5-pro"
    assert "how many facilities?" in kwargs["contents"]
    assert "SYSTEM-RULES" in kwargs["contents"]


def test_blocked_or_empty_response_raises():
    with pytest.raises(RuntimeError, match="no usable text"):
        _provider(None).generate_sql("q", "sys")


def test_empty_after_clean_raises():
    with pytest.raises(RuntimeError, match="empty"):
        _provider("```sql\n\n```").generate_sql("q", "sys")


def test_factory_builds_vertex(monkeypatch):
    from nl_analytics.config import load_settings

    monkeypatch.setenv("NLA_PROVIDER", "vertex")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "hcf-dev-delivery")
    provider = build_provider(load_settings())
    assert provider.name == "vertex"
