"""Tests for the SQL guardrails - the security-critical enforcement point."""

from __future__ import annotations

import sqlglot
from sqlglot import exp

import pytest

from nl_analytics.guardrails import GuardrailError, enforce

DS = "secure_views"


def _limit_value(sql: str) -> int | None:
    node = sqlglot.parse_one(sql, read="bigquery").find(exp.Limit)
    return int(node.expression.name) if node else None


# --- allowed queries -------------------------------------------------------

def test_allows_simple_select():
    result = enforce(f"SELECT age_band FROM {DS}.v_patient_summary")
    assert "v_patient_summary" in result.tables
    assert result.limit == 1000


def test_allows_join_and_aggregate():
    sql = (
        f"SELECT f.region, COUNT(*) c "
        f"FROM {DS}.v_encounter_facts e "
        f"JOIN {DS}.v_facility_dim f USING (facility_id) GROUP BY f.region"
    )
    result = enforce(sql)
    assert set(result.tables) == {"v_encounter_facts", "v_facility_dim"}


def test_allows_cte_without_flagging_cte_name_as_table():
    sql = (
        f"WITH per_fac AS ("
        f"  SELECT facility_id, COUNT(*) c FROM {DS}.v_encounter_facts GROUP BY facility_id"
        f") SELECT * FROM per_fac ORDER BY c DESC"
    )
    result = enforce(sql)
    assert result.tables == ("v_encounter_facts",)


def test_allows_unqualified_table():
    result = enforce("SELECT * FROM v_facility_dim")
    assert result.tables == ("v_facility_dim",)


# --- limit handling --------------------------------------------------------

def test_injects_limit_when_absent():
    result = enforce(f"SELECT * FROM {DS}.v_facility_dim", max_rows=250)
    assert _limit_value(result.sql) == 250


def test_caps_oversized_limit():
    result = enforce(f"SELECT * FROM {DS}.v_facility_dim LIMIT 999999", max_rows=1000)
    assert _limit_value(result.sql) == 1000


def test_keeps_tighter_limit():
    result = enforce(f"SELECT * FROM {DS}.v_facility_dim LIMIT 5", max_rows=1000)
    assert _limit_value(result.sql) == 5


def test_union_is_wrapped_and_limited():
    sql = (
        f"SELECT age_band FROM {DS}.v_patient_summary "
        f"UNION ALL SELECT sex FROM {DS}.v_patient_summary"
    )
    result = enforce(sql, max_rows=100)
    assert _limit_value(result.sql) == 100
    assert result.tables == ("v_patient_summary",)


# --- blocked queries -------------------------------------------------------

@pytest.mark.parametrize(
    "sql",
    [
        f"DELETE FROM {DS}.v_encounter_facts",
        f"UPDATE {DS}.v_encounter_facts SET total_charges = 0",
        f"INSERT INTO {DS}.v_encounter_facts (encounter_key) VALUES ('x')",
        f"DROP TABLE {DS}.v_patient_summary",
        f"ALTER TABLE {DS}.v_patient_summary ADD COLUMN x INT64",
        f"TRUNCATE TABLE {DS}.v_encounter_facts",
        f"MERGE {DS}.v_encounter_facts t USING {DS}.v_facility_dim s "
        f"ON t.facility_id = s.facility_id WHEN MATCHED THEN DELETE",
        f"CREATE TABLE {DS}.x AS SELECT 1 AS a",
    ],
)
def test_blocks_non_read_only(sql):
    with pytest.raises(GuardrailError):
        enforce(sql)


def test_blocks_multiple_statements():
    with pytest.raises(GuardrailError, match="one statement"):
        enforce(f"SELECT 1 FROM {DS}.v_facility_dim; SELECT 2 FROM {DS}.v_facility_dim")


def test_blocks_disallowed_table():
    with pytest.raises(GuardrailError, match="not permitted"):
        enforce("SELECT * FROM curated_phi.encounter")


def test_blocks_raw_phi():
    with pytest.raises(GuardrailError):
        enforce("SELECT * FROM raw_phi.patient")


def test_blocks_wrong_dataset_qualifier():
    with pytest.raises(GuardrailError):
        enforce("SELECT * FROM other_dataset.v_facility_dim")


def test_blocks_empty():
    with pytest.raises(GuardrailError):
        enforce("   ")
