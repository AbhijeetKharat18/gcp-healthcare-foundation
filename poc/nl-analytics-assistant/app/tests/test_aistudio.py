"""AI Studio provider wiring tests (no network: the SDK client is faked)."""

from __future__ import annotations

import pytest
from nl_analytics.llm import build_provider
from nl_analytics.llm.aistudio import AIStudioGeminiProvider


class _FakeResponse:
    def __init__(self, text: str) -> None:
        self.text = text


class _FakeModels:
    def __init__(self, text: str) -> None:
        self._text = text
        self.last_kwargs = None

    def generate_content(self, **kwargs):
        self.last_kwargs = kwargs
        return _FakeResponse(self._text)


class _FakeClient:
    def __init__(self, text: str) -> None:
        self.models = _FakeModels(text)


def _provider_with(text: str) -> AIStudioGeminiProvider:
    p = AIStudioGeminiProvider(api_key="test-key", model="gemini-2.5-flash")
    p._client = _FakeClient(text)  # inject fake, skip real SDK
    return p


def test_requires_api_key():
    with pytest.raises(ValueError, match="API key"):
        AIStudioGeminiProvider(api_key="", model="gemini-2.5-flash")


def test_strips_markdown_fences():
    p = _provider_with("```sql\nSELECT 1 FROM secure_views.v_facility_dim;\n```")
    sql = p.generate_sql("q", "system")
    assert sql == "SELECT 1 FROM secure_views.v_facility_dim"


def test_passes_model_and_prompt():
    p = _provider_with("SELECT 1")
    p.generate_sql("how many facilities?", "SYS")
    kwargs = p._client.models.last_kwargs
    assert kwargs["model"] == "gemini-2.5-flash"
    assert "how many facilities?" in kwargs["contents"]


def test_empty_response_raises():
    p = _provider_with("")
    with pytest.raises(RuntimeError):
        p.generate_sql("q", "system")


def test_empty_after_clean_raises():
    # Non-empty text that cleans to nothing (empty fenced block).
    p = _provider_with("```sql\n\n```")
    with pytest.raises(RuntimeError, match="empty"):
        p.generate_sql("q", "system")


def test_factory_builds_aistudio(monkeypatch):
    from nl_analytics.config import load_settings

    monkeypatch.setenv("NLA_PROVIDER", "aistudio")
    monkeypatch.setenv("NLA_GEMINI_API_KEY", "test-key")
    provider = build_provider(load_settings())
    assert provider.name == "aistudio"


def test_factory_unknown_provider(monkeypatch):
    from nl_analytics.config import load_settings

    monkeypatch.setenv("NLA_PROVIDER", "bogus")
    with pytest.raises(ValueError, match="Unknown NLA_PROVIDER"):
        build_provider(load_settings())
