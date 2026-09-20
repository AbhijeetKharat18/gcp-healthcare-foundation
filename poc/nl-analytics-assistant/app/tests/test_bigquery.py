"""BigQuery executor logic tests with a fake client (no cloud, no network).

google-cloud-bigquery isn't installed in the dev/test env, so we bypass the
SDK-importing __init__ and inject a fake bigquery module + client, exercising
dry_run, execute, row conversion, and _json_safe.
"""

from __future__ import annotations

import datetime as dt
import sys
import types
from decimal import Decimal

import pytest
from nl_analytics.executor.bigquery_exec import BigQueryExecutor


class _Field:
    def __init__(self, name):
        self.name = name


class _Job:
    def __init__(self, rows, schema, total_bytes=1234):
        self._rows = rows
        self.schema = [_Field(n) for n in schema]
        self.total_bytes_processed = total_bytes

    def result(self):
        return self

    def __iter__(self):
        return iter(self._rows)


class _FakeClient:
    def __init__(self, job):
        self._job = job
        self.last_sql = None
        self.last_cfg = None

    def query(self, sql, job_config=None, location=None):
        self.last_sql = sql
        self.last_cfg = job_config
        return self._job


class _FakeBQ:
    def QueryJobConfig(self, **kwargs):
        return kwargs


def _executor_with(job) -> BigQueryExecutor:
    # Bypass __init__ (which imports the SDK); wire fakes directly.
    ex = BigQueryExecutor.__new__(BigQueryExecutor)
    ex._bq = _FakeBQ()
    ex.location = "US"
    ex.max_bytes_billed = 1_000_000
    ex.client = _FakeClient(job)
    return ex


def test_dry_run_returns_bytes():
    ex = _executor_with(_Job(rows=[], schema=["n"], total_bytes=999))
    assert ex.dry_run("SELECT 1") == 999
    assert ex.client.last_cfg["dry_run"] is True


def test_execute_converts_rows_and_types():
    rows = [{"d": dt.date(2026, 1, 2), "amt": Decimal("12.50"), "name": "Cedar"}]
    ex = _executor_with(_Job(rows=rows, schema=["d", "amt", "name"]))
    result = ex.execute("SELECT d, amt, name FROM secure_views.v_facility_dim")
    assert result.columns == ["d", "amt", "name"]
    assert result.rows[0]["d"] == "2026-01-02"       # date -> isoformat
    assert result.rows[0]["amt"] == 12.5              # Decimal -> float
    assert isinstance(result.rows[0]["amt"], float)
    assert result.row_count == 1
    assert result.bytes_processed == 1234
    assert result.engine.startswith("bigquery")


def test_factory_builds_bigquery(monkeypatch):
    # Stub google.cloud.bigquery so the factory can construct the executor.
    fake_bq = types.ModuleType("google.cloud.bigquery")
    fake_bq.Client = lambda project=None, location=None: _FakeClient(_Job([], []))
    fake_bq.QueryJobConfig = lambda **kw: kw
    google = types.ModuleType("google")
    google_cloud = types.ModuleType("google.cloud")
    google_cloud.bigquery = fake_bq
    google.cloud = google_cloud
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.cloud", google_cloud)
    monkeypatch.setitem(sys.modules, "google.cloud.bigquery", fake_bq)

    from nl_analytics.config import load_settings
    from nl_analytics.executor import build_executor

    monkeypatch.setenv("NLA_EXECUTOR", "bigquery")
    monkeypatch.setenv("GOOGLE_CLOUD_PROJECT", "hcf-dev-lakehouse")
    ex = build_executor(load_settings())
    assert ex.name == "bigquery"


def test_factory_unknown_executor(monkeypatch):
    from nl_analytics.config import load_settings
    from nl_analytics.executor import build_executor

    monkeypatch.setenv("NLA_EXECUTOR", "bogus")
    with pytest.raises(ValueError, match="Unknown NLA_EXECUTOR"):
        build_executor(load_settings())
