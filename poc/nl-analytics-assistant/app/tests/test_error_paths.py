"""Service orchestration error paths and the mock fallback."""

from __future__ import annotations

from nl_analytics.executor.base import QueryResult
from nl_analytics.llm.mock import MockProvider
from nl_analytics.service import AnalyticsService


class _Provider:
    name = "fake"

    def __init__(self, sql="SELECT 1 FROM secure_views.v_facility_dim", raise_exc=None):
        self._sql = sql
        self._raise = raise_exc

    def generate_sql(self, question, system_prompt):
        if self._raise:
            raise self._raise
        return self._sql


class _Executor:
    name = "fake"

    def __init__(self, dry_exc=None, exec_exc=None):
        self._dry_exc = dry_exc
        self._exec_exc = exec_exc

    def dry_run(self, sql):
        if self._dry_exc:
            raise self._dry_exc
        return None

    def execute(self, sql):
        if self._exec_exc:
            raise self._exec_exc
        return QueryResult(columns=["n"], rows=[{"n": 1}], row_count=1, engine="fake")


def _svc(provider, executor):
    return AnalyticsService(provider=provider, executor=executor)


def test_generation_failure_reports_stage_generate():
    svc = _svc(_Provider(raise_exc=RuntimeError("model down")), _Executor())
    r = svc.ask("anything")
    assert not r.ok and r.stage == "generate"
    assert "model down" in r.error


def test_dry_run_failure_reports_stage_dry_run():
    svc = _svc(_Provider(), _Executor(dry_exc=RuntimeError("bad query")))
    r = svc.ask("anything")
    assert not r.ok and r.stage == "dry_run"
    assert r.elapsed_ms >= 0


def test_execute_failure_reports_stage_execute():
    svc = _svc(_Provider(), _Executor(exec_exc=RuntimeError("boom")))
    r = svc.ask("anything")
    assert not r.ok and r.stage == "execute"


def test_happy_path_with_fakes():
    svc = _svc(_Provider(), _Executor())
    r = svc.ask("anything")
    assert r.ok and r.row_count == 1 and r.tables_used == ["v_facility_dim"]


class _BytesExecutor:
    name = "fake"

    def dry_run(self, sql):
        return 4096  # estimated bytes (dry-run path)

    def execute(self, sql):
        return QueryResult(
            columns=["n"], rows=[{"n": 1}], row_count=1,
            bytes_processed=8192, engine="fake",
        )


def test_bytes_processed_propagated():
    svc = _svc(_Provider(), _BytesExecutor())
    r = svc.ask("anything")
    assert r.ok
    assert r.bytes_processed == 8192  # execute value wins over the dry-run estimate


def test_mock_fallback_for_unknown_question():
    # A question matching no rule falls back to a safe encounter-count query.
    sql = MockProvider().generate_sql("something totally unrelated", "sys")
    assert "v_encounter_facts" in sql
    assert sql.lower().startswith("select")
