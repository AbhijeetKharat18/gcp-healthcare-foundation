"""Catalog invariants: the allowlist must never expose ungoverned datasets."""

from __future__ import annotations

from nl_analytics.catalog import ALLOWED_TABLES, TABLES, schema_prompt

UNGOVERNED = {"raw_phi", "standardized_phi", "curated_phi", "deidentified", "analytics_mart"}


def test_only_secure_views_are_allowed():
    # Every allowed object is a secure view (v_ prefix), and no ungoverned
    # dataset name leaks into the allowlist.
    assert all(name.startswith("v_") for name in ALLOWED_TABLES)
    assert not (ALLOWED_TABLES & UNGOVERNED)


def test_no_direct_identifier_columns():
    forbidden = {"name", "mrn", "ssn", "dob", "date_of_birth", "phone", "email", "address"}
    for table in TABLES:
        cols = {c.name.lower() for c in table.columns}
        assert not (cols & forbidden), f"{table.name} exposes a direct identifier"


def test_schema_prompt_lists_every_table():
    prompt = schema_prompt()
    for table in TABLES:
        assert table.name in prompt
