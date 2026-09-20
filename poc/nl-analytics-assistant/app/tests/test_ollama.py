"""Ollama provider wiring tests (no network: the HTTP client is faked)."""

from __future__ import annotations

import pytest
from nl_analytics.llm import build_provider
from nl_analytics.llm.ollama import OllamaProvider


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    def __init__(self, payload: dict) -> None:
        self._payload = payload
        self.last_url = None
        self.last_json = None

    def post(self, url, json):  # mirrors httpx.Client.post signature
        self.last_url = url
        self.last_json = json
        return _FakeResponse(self._payload)


def _provider_with(response_text: str) -> OllamaProvider:
    p = OllamaProvider(host="http://localhost:11434", model="llama3.1")
    p._client = _FakeClient({"response": response_text})
    return p


def test_extracts_sql_from_prose_and_fences():
    # A chatty local model wrapping SQL in prose + a code fence.
    text = "Sure! Here is the query:\n```sql\nSELECT COUNT(*) FROM secure_views.v_facility_dim;\n```\nHope that helps."
    p = _provider_with(text)
    assert p.generate_sql("q", "sys") == "SELECT COUNT(*) FROM secure_views.v_facility_dim"


def test_strips_leading_prose_without_fence():
    text = "Here is the SQL: SELECT 1 FROM secure_views.v_facility_dim"
    p = _provider_with(text)
    assert p.generate_sql("q", "sys").upper().startswith("SELECT 1")


def test_sends_model_and_host():
    p = _provider_with("SELECT 1")
    p.generate_sql("how many?", "SYS")
    assert p._client.last_url == "http://localhost:11434/api/generate"
    assert p._client.last_json["model"] == "llama3.1"
    assert p._client.last_json["stream"] is False
    assert p._client.last_json["options"]["temperature"] == 0


def test_empty_response_raises():
    p = _provider_with("")
    with pytest.raises(RuntimeError):
        p.generate_sql("q", "sys")


class _RaisingClient:
    def post(self, url, json):  # mirrors httpx.Client.post signature
        raise ConnectionError("connection refused")


def test_unreachable_server_raises_clean_error():
    p = OllamaProvider(host="http://localhost:11434", model="llama3.1")
    p._client = _RaisingClient()
    with pytest.raises(RuntimeError, match="Could not reach Ollama"):
        p.generate_sql("q", "sys")


def test_host_trailing_slash_normalised():
    p = OllamaProvider(host="http://localhost:11434/", model="m")
    assert p.host == "http://localhost:11434"


def test_factory_builds_ollama(monkeypatch):
    from nl_analytics.config import load_settings

    monkeypatch.setenv("NLA_PROVIDER", "ollama")
    monkeypatch.setenv("NLA_OLLAMA_MODEL", "qwen2.5-coder")
    provider = build_provider(load_settings())
    assert provider.name == "ollama"
    assert provider.model == "qwen2.5-coder"
