"""Shared helper to normalise raw LLM output into bare SQL."""

from __future__ import annotations

import re

_FENCE = re.compile(r"^```(?:sql)?\s*|\s*```$", re.IGNORECASE | re.MULTILINE)


def clean_sql(text: str) -> str:
    """Strip markdown fences and surrounding whitespace from model output."""
    if not text:
        return ""
    cleaned = _FENCE.sub("", text).strip()
    # Some models prefix a stray "sql" token on its own line.
    if cleaned.lower().startswith("sql\n"):
        cleaned = cleaned[4:].strip()
    return cleaned.rstrip(";").strip()
