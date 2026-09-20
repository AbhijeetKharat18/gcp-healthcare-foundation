"""DuckDB executor tests, including the qualified/unqualified resolution path."""

from __future__ import annotations

import pytest
from nl_analytics.config import load_settings
from nl_analytics.executor.duckdb_exec import DuckDBExecutor
from nl_analytics.guardrails import enforce


@pytest.fixture(scope="module")
def executor() -> DuckDBExecutor:
    return DuckDBExecutor(load_settings().data_dir)


def test_qualified_query_executes(executor):
    result = executor.execute("SELECT COUNT(*) AS n FROM secure_views.v_facility_dim")
    assert result.rows == [{"n": 5}]
    assert result.engine.startswith("duckdb")


def test_unqualified_query_resolves(executor):
    # search_path fallback: bare allow-listed name still resolves locally.
    result = executor.execute("SELECT COUNT(*) AS n FROM v_facility_dim")
    assert result.rows == [{"n": 5}]


def test_guardrail_output_executes(executor):
    # The exact SQL the guardrails emit for an unqualified question must run.
    guarded = enforce("SELECT COUNT(*) AS n FROM v_encounter_facts")
    result = executor.execute(guarded.sql)
    assert result.row_count == 1
    assert result.rows[0]["n"] > 0


def test_bigquery_dialect_functions_transpile(executor):
    # COUNTIF / SAFE_DIVIDE are BigQuery-isms; they must transpile and run.
    sql = (
        "SELECT ROUND(SAFE_DIVIDE(COUNTIF(is_readmission_30d), COUNT(*)) * 100, 1) AS pct "
        "FROM secure_views.v_encounter_facts WHERE encounter_type = 'Inpatient'"
    )
    result = executor.execute(sql)
    assert result.row_count == 1
    assert "pct" in result.columns


def test_json_safe_types(executor):
    # DATE -> isoformat string; NUMERIC -> float.
    sql = (
        "SELECT admit_date, total_charges FROM secure_views.v_encounter_facts "
        "ORDER BY admit_date LIMIT 1"
    )
    row = executor.execute(sql).rows[0]
    assert isinstance(row["admit_date"], str)
    assert isinstance(row["total_charges"], (int, float))


def test_missing_data_dir_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="synthetic"):
        DuckDBExecutor(tmp_path)  # empty dir, no CSVs
