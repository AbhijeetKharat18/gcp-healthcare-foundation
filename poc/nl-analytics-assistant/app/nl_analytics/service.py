"""Orchestration: question -> SQL -> guardrails -> execute -> answer.

This is the whole pipeline in one place, deliberately readable so the trust
boundary is obvious:

    question
      -> LLM (grounded on the secure_views catalog only)
      -> guardrails.enforce  (SELECT-only, allowlist, LIMIT)   <-- trust gate
      -> executor.dry_run    (cost / validity check)
      -> executor.execute    (reads secure_views only)
      -> answer (+ the exact SQL, for transparency)
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from typing import Any

from .config import Settings, load_settings
from .executor import QueryExecutor, build_executor
from .guardrails import GuardrailError, enforce
from .llm import LLMProvider, build_provider
from .prompt import build_system_prompt

logger = logging.getLogger("nl_analytics")


@dataclass
class AskResult:
    question: str
    ok: bool
    sql: str | None = None
    columns: list[str] = field(default_factory=list)
    rows: list[dict[str, Any]] = field(default_factory=list)
    row_count: int = 0
    tables_used: list[str] = field(default_factory=list)
    provider: str = ""
    executor: str = ""
    engine: str = ""
    bytes_processed: int | None = None
    elapsed_ms: int = 0
    error: str | None = None
    stage: str | None = None  # where it failed: generate | guardrail | dry_run | execute

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class AnalyticsService:
    def __init__(
        self,
        settings: Settings | None = None,
        provider: LLMProvider | None = None,
        executor: QueryExecutor | None = None,
    ) -> None:
        self.settings = settings or load_settings()
        self.provider = provider or build_provider(self.settings)
        self.executor = executor or build_executor(self.settings)
        self.system_prompt = build_system_prompt(self.settings.logical_dataset)

    def ask(self, question: str) -> AskResult:
        started = time.perf_counter()
        result = AskResult(
            question=question,
            ok=False,
            provider=getattr(self.provider, "name", "unknown"),
            executor=getattr(self.executor, "name", "unknown"),
        )

        if not question or not question.strip():
            result.error = "Question is empty."
            result.stage = "generate"
            return result

        # 1. Generate.
        try:
            raw_sql = self.provider.generate_sql(question, self.system_prompt)
        except Exception as exc:  # noqa: BLE001
            logger.exception("LLM generation failed")
            result.error = f"Could not generate SQL: {exc}"
            result.stage = "generate"
            return result

        # 2. Guardrails (the trust gate).
        try:
            guarded = enforce(
                raw_sql,
                max_rows=self.settings.max_rows,
            )
        except GuardrailError as exc:
            logger.warning("Guardrail rejected query: %s", exc)
            result.sql = raw_sql
            result.error = f"Query blocked by guardrails: {exc}"
            result.stage = "guardrail"
            return result

        result.sql = guarded.sql
        result.tables_used = list(guarded.tables)

        # 3. Dry-run (validity / cost).
        try:
            estimated = self.executor.dry_run(guarded.sql)
            if estimated is not None:
                result.bytes_processed = estimated
        except Exception as exc:  # noqa: BLE001
            logger.warning("Dry-run failed: %s", exc)
            result.error = f"Query failed validation: {exc}"
            result.stage = "dry_run"
            result.elapsed_ms = _ms(started)
            return result

        # 4. Execute.
        try:
            query_result = self.executor.execute(guarded.sql)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Execution failed")
            result.error = f"Query execution failed: {exc}"
            result.stage = "execute"
            result.elapsed_ms = _ms(started)
            return result

        result.ok = True
        result.columns = query_result.columns
        result.rows = query_result.rows
        result.row_count = query_result.row_count
        result.engine = query_result.engine
        if query_result.bytes_processed is not None:
            result.bytes_processed = query_result.bytes_processed
        result.elapsed_ms = _ms(started)
        return result


def _ms(started: float) -> int:
    return int((time.perf_counter() - started) * 1000)
