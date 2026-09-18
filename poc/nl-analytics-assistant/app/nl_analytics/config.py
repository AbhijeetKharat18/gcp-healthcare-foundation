"""Runtime configuration, sourced from environment variables.

Defaults are tuned for the **offline local demo** (mock LLM + DuckDB over
synthetic data) so the app runs with zero cloud dependencies. The Terraform
serving layer overrides these to run against Vertex AI + BigQuery.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Repo-relative default location of the generated synthetic data.
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    # Which components to use.
    provider: str = os.getenv("NLA_PROVIDER", "mock")          # "vertex" | "mock"
    executor: str = os.getenv("NLA_EXECUTOR", "duckdb")        # "bigquery" | "duckdb"

    # BigQuery target (production path).
    gcp_project: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    bq_dataset: str = os.getenv("NLA_BQ_DATASET", "secure_views")
    bq_location: str = os.getenv("NLA_BQ_LOCATION", "US")

    # Vertex AI (production path).
    vertex_project: str = os.getenv("NLA_VERTEX_PROJECT", os.getenv("GOOGLE_CLOUD_PROJECT", ""))
    vertex_location: str = os.getenv("NLA_VERTEX_LOCATION", "us-central1")
    vertex_model: str = os.getenv("NLA_VERTEX_MODEL", "gemini-2.5-pro")

    # Local demo data (DuckDB executor).
    data_dir: Path = Path(os.getenv("NLA_DATA_DIR", str(_DEFAULT_DATA_DIR)))

    # Guardrail limits.
    max_rows: int = int(os.getenv("NLA_MAX_ROWS", "1000"))
    max_bytes_billed: int = int(os.getenv("NLA_MAX_BYTES_BILLED", str(1_000_000_000)))  # 1 GB

    @property
    def logical_dataset(self) -> str:
        """Dataset name used to qualify tables in generated SQL."""
        return self.bq_dataset


def load_settings() -> Settings:
    return Settings()
