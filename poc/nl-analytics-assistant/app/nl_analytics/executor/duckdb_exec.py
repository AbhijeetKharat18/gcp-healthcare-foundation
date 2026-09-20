"""Local DuckDB executor over the synthetic secure_views data.

Powers the offline demo. It loads the generated CSVs into a ``secure_views``
schema so the *same* qualified table names used against BigQuery resolve
locally, then transpiles the BigQuery SQL to the DuckDB dialect. This keeps the
demo faithful: the LLM emits real BigQuery Standard SQL and it is validated by
the same guardrails that guard the cloud path.
"""

from __future__ import annotations

import datetime as dt
import threading
from decimal import Decimal
from pathlib import Path
from typing import Any

import sqlglot
from sqlglot import exp

from .base import QueryResult


class DuckDBExecutor:
    name = "duckdb"

    def __init__(self, data_dir: Path, max_rows: int = 1000) -> None:
        import duckdb

        self.max_rows = max_rows
        self._con = duckdb.connect(database=":memory:")
        # A DuckDB connection is not safe for concurrent use, and uvicorn serves
        # sync endpoints from a threadpool. Serialize access so concurrent
        # requests can't clobber each other's result set. (Queries here run on a
        # tiny in-memory DB in sub-millisecond time; the concurrent production
        # path is BigQuery, whose client is thread-safe.)
        self._lock = threading.Lock()
        self._load(data_dir)

    def _load(self, data_dir: Path) -> None:
        csvs = sorted(Path(data_dir).glob("*.csv"))
        if not csvs:
            raise FileNotFoundError(
                f"No synthetic CSVs in {data_dir}. Run data/generate_synthetic.py first."
            )
        self._con.execute("CREATE SCHEMA IF NOT EXISTS secure_views")
        for csv in csvs:
            table = csv.stem
            self._con.execute(
                f'CREATE OR REPLACE TABLE secure_views."{table}" AS '
                "SELECT * FROM read_csv_auto(?, header=true, sample_size=-1)",
                [str(csv)],
            )
        # Defensive: resolve bare table names to the secure_views schema too, so
        # the executor works even if handed an unqualified (but allow-listed)
        # query directly.
        self._con.execute("SET search_path = 'main,secure_views'")

    @staticmethod
    def _to_duckdb(sql: str) -> str:
        tree = sqlglot.parse_one(sql, read="bigquery")
        # Drop any project/catalog qualifier so `proj.secure_views.v_x` and
        # `secure_views.v_x` both resolve to the local schema.table.
        for table in tree.find_all(exp.Table):
            if table.args.get("catalog"):
                table.set("catalog", None)
        return tree.sql(dialect="duckdb")

    def dry_run(self, sql: str) -> int | None:
        local_sql = self._to_duckdb(sql)
        with self._lock:
            self._con.execute(f"EXPLAIN {local_sql}")
        return None

    def execute(self, sql: str) -> QueryResult:
        local_sql = self._to_duckdb(sql)
        # Hold the lock across execute+fetch: the cursor is tied to the shared
        # connection, so the fetch must not interleave with another query.
        with self._lock:
            cur = self._con.execute(local_sql)
            columns = [d[0] for d in cur.description]
            raw = cur.fetchmany(self.max_rows)
        rows = [
            dict(zip(columns, (_json_safe(v) for v in record), strict=True))
            for record in raw
        ]
        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=len(rows),
            bytes_processed=None,
            engine="duckdb (local synthetic data)",
        )


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, (dt.date, dt.datetime)):
        return value.isoformat()
    return value
