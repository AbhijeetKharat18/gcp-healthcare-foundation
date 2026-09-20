"""Vertex provider logic tests with a stubbed Vertex SDK (no cloud, no network).

The vertexai SDK isn't installed in the dev/test env, so we inject fake
`vertexai` modules into sys.modules and a fake model, exercising the provider's
own logic (prompt assembly, response handling, clean_sql) without any cloud.
"""

from __future__ import annotations

import sys
import types

import pytest
from nl_analytics.llm import build_provider
from nl_analytics.llm.vertex import VertexGeminiProvider


class _FakeResp:
    def __init__(self, text):
        self._text = text

    @property
    def text(self):
        if self._text is None:
            raise ValueError("no candidates")
        return self._text


class _FakeModel:
    def __init__(self, text):
        self._text = text
        self.last_prompt = None
        self.last_config = None

    def generate_content(self, prompt, generation_config=None):
        self.last_prompt = prompt
        self.last_config = generation_config
        return _FakeResp(self._text)


@pytest.fixture(autouse=True)
def _stub_vertex_sdk(monkeypatch):
    """Provide fake `vertexai` + `vertexai.generative_models` modules."""
    gm = types.ModuleType("vertexai.generative_models")
    gm.GenerationConfig = lambda **kw: kw  # config is opaque to our test
    gm.GenerativeModel = lambda name: _FakeModel("SELECT 1")
    vx = types.ModuleType("vertexai")
    vx.init = lambda **kw: None
    vx.generative_models = gm
    monkeypatch.setitem(sys.modules, "vertexai", vx)
    monkeypatch.setitem(sys.modules, "vertexai.generative_models", gm)
    yield


def _provider(text) -> VertexGeminiProvider:
    p = VertexGeminiProvider(project="p", location="us-central1", model="gemini-2.5-pro")
    p._model = _FakeModel(text)  # skip real GenerativeModel construction
    return p


def test_requires_project():
    with pytest.raises(ValueError, match="requires a project"):
        VertexGeminiProvider(project="", location="us-central1", model="m")


def test_generates_and_cleans_sql():
    p = _provider("```sql\nSELECT 1 FROM secure_views.v_facility_dim;\n```")
    assert p.generate_sql("q", "sys") == "SELECT 1 FROM secure_views.v_facility_dim"


def test_prompt_includes_question_and_system():
    p = _provider("SELECT 1")
    p.generate_sql("how many facilities?", "SYSTEM-RULES")
    assert "how many facilities?" in p._model.last_prompt
    assert "SYSTEM-RULES" in p._model.last_prompt


def test_blocked_response_raises():
    p = _provider(None)  # response.text raises -> handled
    with pytest.raises(RuntimeError, match="no usable text"):
        p.generate_sql("q", "sys")


def test_empty_after_clean_raises():
    p = _provider("```sql\n\n```")  # cleans to empty
    with pytest.raises(RuntimeError, match="empty"):
        p.generate_sql("q", "sys")


def test_get_model_builds_once():
    p = VertexGeminiProvider(project="p", location="l", model="m")
    m1 = p._get_model()
    m2 = p._get_model()
    assert m1 is m2  # cached


def test_factory_builds_vertex(monkeypatch):
    from nl_analytics.config import load_settings

    monkeypatch.setenv("NLA_PROVIDER", "vertex")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "hcf-dev-delivery")
    provider = build_provider(load_settings())
    assert provider.name == "vertex"
