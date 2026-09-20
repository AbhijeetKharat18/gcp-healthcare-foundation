"""Shared helper to normalise raw LLM output into bare SQL.

Robust against the ways models (especially smaller local ones) wrap output:
markdown code fences, a leading "Here is the query:" preamble, or a stray
language token. Anything the model adds that this doesn't strip will simply be
rejected by the guardrails, so this only needs to handle the common cases.
"""

from __future__ import annotations

import re

# A fenced ```sql ... ``` (or plain ``` ... ```) block, if present.
_CODE_BLOCK = re.compile(r"```(?:sql)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)
# The start of an actual query, to drop any leading prose.
_QUERY_START = re.compile(r"(?is)\b(WITH|SELECT)\b")


def clean_sql(text: str) -> str:
    """Extract bare SQL from a model response."""
    if not text:
        return ""
    stripped = text.strip()

    # 1. Prefer the contents of a fenced code block.
    block = _CODE_BLOCK.search(stripped)
    if block:
        stripped = block.group(1).strip()
    else:
        # 2. Otherwise drop any leading prose before the first WITH/SELECT.
        start = _QUERY_START.search(stripped)
        if start:
            stripped = stripped[start.start():].strip()

    return stripped.rstrip(";").strip()
