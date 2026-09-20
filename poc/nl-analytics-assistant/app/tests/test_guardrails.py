"""Tests for the SQL guardrails - the security-critical enforcement point."""

from __future__ import annotations

import pytest
import sqlglot
from nl_analytics.guardrails import GuardrailError, enforce
from sqlglot import exp

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


def test_qualifies_unqualified_table():
    # Unqualified but allow-listed tables are normalised to secure_views.<table>
    # so the executed SQL never depends on a default dataset.
    result = enforce("SELECT COUNT(*) AS n FROM v_facility_dim")
    normalised = result.sql.replace("`", "")
    assert "secure_views.v_facility_dim" in normalised


def test_preserves_existing_dataset_qualifier():
    result = enforce(f"SELECT * FROM {DS}.v_patient_summary")
    assert result.sql.replace("`", "").count("secure_views.v_patient_summary") == 1


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


def test_non_literal_limit_is_overridden():
    # A LIMIT that isn't a plain integer literal (here a query parameter) can't
    # be compared, so it is replaced with the safe max.
    result = enforce(f"SELECT * FROM {DS}.v_facility_dim LIMIT @n", max_rows=1000)
    assert _limit_value(result.sql) == 1000


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
        f"CREATE VIEW {DS}.hack AS SELECT 1",
        # EXPORT DATA exfiltrates query results to GCS - must be blocked even
        # though its inner SELECT only reads secure_views.
        f"EXPORT DATA OPTIONS(uri='gs://x/*') AS SELECT * FROM {DS}.v_facility_dim",
        "CALL some.procedure()",
        f"GRANT SELECT ON {DS}.v_facility_dim TO 'x'",
    ],
)
def test_blocks_non_read_only(sql):
    with pytest.raises(GuardrailError):
        enforce(sql)


def test_blocks_phi_hidden_in_cte():
    with pytest.raises(GuardrailError):
        enforce("WITH x AS (SELECT * FROM curated_phi.encounter) SELECT * FROM x")


def test_blocks_other_dataset_in_subquery():
    with pytest.raises(GuardrailError):
        enforce(
            f"SELECT (SELECT COUNT(*) FROM deidentified.foo) AS c "
            f"FROM {DS}.v_facility_dim"
        )


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
