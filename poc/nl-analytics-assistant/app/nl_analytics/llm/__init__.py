"""LLM provider abstraction: pick the text->SQL backend at runtime."""

from __future__ import annotations

from ..config import Settings
from .base import LLMProvider
from .mock import MockProvider


def build_provider(settings: Settings) -> LLMProvider:
    """Instantiate the configured LLM provider.

    ``vertex`` is imported lazily so the offline demo and the test suite do not
    need the Vertex AI SDK installed.
    """
    provider = settings.provider.lower()
    if provider == "mock":
        return MockProvider()
    if provider == "vertex":
        from .vertex import VertexGeminiProvider

        return VertexGeminiProvider(
            project=settings.vertex_project,
            location=settings.vertex_location,
            model=settings.vertex_model,
        )
    if provider == "aistudio":
        from .aistudio import AIStudioGeminiProvider

        return AIStudioGeminiProvider(
            api_key=settings.gemini_api_key,
            model=settings.aistudio_model,
        )
    if provider == "ollama":
        from .ollama import OllamaProvider

        return OllamaProvider(
            host=settings.ollama_host,
            model=settings.ollama_model,
        )
    raise ValueError(
        f"Unknown NLA_PROVIDER: {settings.provider!r} "
        "(use 'vertex', 'aistudio', 'ollama', or 'mock')."
    )


__all__ = ["LLMProvider", "MockProvider", "build_provider"]
