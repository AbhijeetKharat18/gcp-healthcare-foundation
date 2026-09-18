"""The LLM provider contract."""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class LLMProvider(Protocol):
    """Turns a natural-language question into a single BigQuery SQL query.

    Implementations must return raw SQL only (no markdown fences, no prose).
    Grounding, dialect, and safety rules are supplied by the caller in
    ``system_prompt``; the provider is responsible only for the model call.
    """

    name: str

    def generate_sql(self, question: str, system_prompt: str) -> str:
        ...
