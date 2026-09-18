"""The query executor contract."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(frozen=True)
class QueryResult:
    columns: list[str]
    rows: list[dict[str, Any]]
    row_count: int
    # Optional cost/telemetry the UI can surface (e.g. BigQuery bytes scanned).
    bytes_processed: int | None = None
    engine: str = ""


@runtime_checkable
class QueryExecutor(Protocol):
    name: str

    def dry_run(self, sql: str) -> int | None:
        """Validate/estimate the query without returning rows.

        Returns estimated bytes processed when the backend supports it, else
        ``None``. Raises on invalid SQL.
        """
        ...

    def execute(self, sql: str) -> QueryResult:
        ...
