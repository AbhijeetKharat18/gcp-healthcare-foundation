"""Query executor abstraction: run sanitised SQL against a backend."""

from __future__ import annotations

from ..config import Settings
from .base import QueryExecutor, QueryResult


def build_executor(settings: Settings) -> QueryExecutor:
    """Instantiate the configured executor.

    Backends are imported lazily so the demo doesn't need the BigQuery client
    and a BigQuery deployment doesn't need DuckDB.
    """
    executor = settings.executor.lower()
    if executor == "duckdb":
        from .duckdb_exec import DuckDBExecutor

        return DuckDBExecutor(data_dir=settings.data_dir, max_rows=settings.max_rows)
    if executor == "bigquery":
        from .bigquery_exec import BigQueryExecutor

        return BigQueryExecutor(
            project=settings.gcp_project,
            location=settings.bq_location,
            max_bytes_billed=settings.max_bytes_billed,
        )
    raise ValueError(
        f"Unknown NLA_EXECUTOR: {settings.executor!r} (use 'bigquery' or 'duckdb')."
    )


__all__ = ["QueryExecutor", "QueryResult", "build_executor"]
