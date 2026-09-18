"""SQL guardrails - the enforcement point that makes text->SQL safe.

Every query produced by the LLM passes through :func:`enforce` before it is
allowed anywhere near a database. This is defence-in-depth *on top of* the IAM
boundary (``sa-delivery`` can only read ``secure_views``): even if a prompt
injection convinced the model to emit destructive or out-of-scope SQL, it never
executes.

Rules enforced:
  1. Parses as exactly one statement (no stacked queries).
  2. Is a read-only query (SELECT / WITH ... SELECT / set operations only).
     Any DML/DDL/DCL or procedural command is rejected.
  3. References only allow-listed ``secure_views`` tables - never raw_phi,
     standardized_phi, or curated_phi.
  4. Carries a row LIMIT no greater than the configured maximum (injected or
     capped as needed).
"""

from __future__ import annotations

from dataclasses import dataclass

import sqlglot
from sqlglot import exp

from .catalog import ALLOWED_TABLES

_DIALECT = "bigquery"

# The statement's root must be one of these query types. A positive allowlist
# fails closed: any statement type we don't explicitly recognise as a read-only
# query (EXPORT DATA, CREATE, CALL, ...) is rejected, even ones added in future
# sqlglot versions. Names are resolved defensively across versions.
_QUERY_ROOT_NAMES = ["Select", "Union", "Intersect", "Except", "SetOperation", "Subquery"]
_QUERY_ROOTS = tuple(getattr(exp, n) for n in _QUERY_ROOT_NAMES if hasattr(exp, n))

# Expression types that must never appear anywhere (defence in depth on top of
# the root-type allowlist). Resolved defensively so the module keeps working
# across sqlglot versions that add/rename node types.
_FORBIDDEN_NAMES = [
    "Insert", "Update", "Delete", "Merge", "Create", "Drop", "Alter",
    "AlterTable", "TruncateTable", "Command", "Grant", "Set", "SetItem",
    "Use", "Copy", "Pragma", "Transaction", "Commit", "Rollback", "Export",
]
_FORBIDDEN = tuple(getattr(exp, n) for n in _FORBIDDEN_NAMES if hasattr(exp, n))


class GuardrailError(ValueError):
    """Raised when generated SQL violates a safety rule."""


@dataclass(frozen=True)
class GuardrailResult:
    sql: str                 # sanitised SQL, ready to execute (BigQuery dialect)
    tables: tuple[str, ...]  # allow-listed tables referenced
    limit: int               # effective row limit


def enforce(sql: str, allowed_tables: frozenset[str] = ALLOWED_TABLES,
            max_rows: int = 1000) -> GuardrailResult:
    """Validate and sanitise ``sql``; return the safe query or raise."""
    if not sql or not sql.strip():
        raise GuardrailError("Empty query.")

    # 1. Single statement.
    try:
        statements = sqlglot.parse(sql, read=_DIALECT)
    except Exception as exc:  # noqa: BLE001 - surface a clean message
        raise GuardrailError(f"Could not parse SQL: {exc}") from exc

    statements = [s for s in statements if s is not None]
    if len(statements) != 1:
        raise GuardrailError(
            f"Exactly one statement is allowed; found {len(statements)}."
        )
    expr = statements[0]

    # 2. Read-only. The root must be a query (positive allowlist, fails closed),
    #    and no DML/DDL/command node may appear anywhere (defence in depth).
    if not isinstance(expr, _QUERY_ROOTS):
        raise GuardrailError("Only read-only SELECT queries are permitted.")
    if next(iter(expr.find_all(*_FORBIDDEN)), None) is not None:
        raise GuardrailError("Only read-only SELECT queries are permitted.")
    if expr.find(exp.Select) is None:
        raise GuardrailError("Query must be a SELECT.")

    # 3. Table allowlist (also blocks qualifying into a different dataset).
    # CTE names look like table references; they are not real tables, so exclude
    # any unqualified reference whose name is a locally-defined CTE.
    cte_names = {cte.alias_or_name for cte in expr.find_all(exp.CTE)}
    referenced: list[str] = []
    for table in expr.find_all(exp.Table):
        name = table.name
        dataset = table.db  # may be "" if unqualified
        if not dataset and name in cte_names:
            continue
        if name not in allowed_tables:
            raise GuardrailError(
                f"Table {_qualify(table)!r} is not permitted. Allowed: "
                f"{', '.join(sorted(allowed_tables))}."
            )
        if dataset and dataset != "secure_views":
            raise GuardrailError(
                f"Only the 'secure_views' dataset may be queried, not {dataset!r}."
            )
        # Normalise to a fully-qualified secure_views.<table> reference so the
        # executed SQL never depends on a default dataset (and resolves the same
        # against BigQuery and the local DuckDB schema).
        if not dataset:
            table.set("db", exp.to_identifier("secure_views"))
        referenced.append(name)

    # 4. Row limit (inject or cap).
    safe_expr = _apply_limit(expr, max_rows)

    return GuardrailResult(
        sql=safe_expr.sql(dialect=_DIALECT, pretty=True),
        tables=tuple(dict.fromkeys(referenced)),  # de-duped, order-preserving
        limit=max_rows,
    )


def _qualify(table: exp.Table) -> str:
    parts = [p for p in (table.catalog, table.db, table.name) if p]
    return ".".join(parts)


def _apply_limit(expr: exp.Expression, max_rows: int) -> exp.Expression:
    """Ensure a LIMIT <= max_rows without dropping an existing tighter one."""
    if isinstance(expr, exp.Select):
        existing = expr.args.get("limit")
        if existing is None:
            return expr.limit(max_rows)
        try:
            current = int(existing.expression.name)
        except (AttributeError, ValueError):
            return expr.limit(max_rows)
        return expr.limit(max_rows) if current > max_rows else expr
    # Set operations (UNION/INTERSECT/EXCEPT) and anything else: wrap and cap.
    return exp.select("*").from_(expr.subquery(alias="_capped")).limit(max_rows)
