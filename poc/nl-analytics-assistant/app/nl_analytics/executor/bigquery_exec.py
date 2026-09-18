"""BigQuery executor (production path).

Runs as ``sa-delivery`` inside the delivery project. That identity can only read
the ``secure_views`` dataset, so the database itself enforces the governance
boundary; the dry-run + ``maximum_bytes_billed`` cap add cost safety on top.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from typing import Any

from .base import QueryResult


class BigQueryExecutor:
    name = "bigquery"

    def __init__(self, project: str, location: str, max_bytes_billed: int) -> None:
        from google.cloud import bigquery

        self._bq = bigquery
        self.location = location or None
        self.max_bytes_billed = max_bytes_billed
        self.client = bigquery.Client(project=project or None, location=self.location)

    def dry_run(self, sql: str) -> int | None:
        cfg = self._bq.QueryJobConfig(dry_run=True, use_query_cache=False)
        job = self.client.query(sql, job_config=cfg, location=self.location)
        return job.total_bytes_processed

    def execute(self, sql: str) -> QueryResult:
        cfg = self._bq.QueryJobConfig(maximum_bytes_billed=self.max_bytes_billed)
        job = self.client.query(sql, job_config=cfg, location=self.location)
        result = job.result()
        columns = [field.name for field in result.schema]
        rows = [
            {col: _json_safe(row[col]) for col in columns}
            for row in result
        ]
        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            bytes_processed=job.total_bytes_processed,
            engine="bigquery (secure_views)",
        )


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value
