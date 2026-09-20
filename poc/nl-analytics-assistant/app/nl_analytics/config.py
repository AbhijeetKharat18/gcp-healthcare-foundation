"""Runtime configuration, sourced from environment variables.

Defaults are tuned for the **offline local demo** (mock LLM + DuckDB over
synthetic data) so the app runs with zero cloud dependencies. The Terraform
serving layer overrides these to run against Vertex AI + BigQuery.

Environment is read in :func:`load_settings` (not at import time), so the same
process always reflects the current environment and tests can override it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

# Repo-relative default location of the generated synthetic data.
_DEFAULT_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "synthetic"

_DEFAULT_MAX_BYTES_BILLED = 1_000_000_000  # 1 GB


@dataclass(frozen=True)
class Settings:
    # Which components to use.
    provider: str = "mock"       # "vertex" | "aistudio" | "mock"
    executor: str = "duckdb"     # "bigquery" | "duckdb"

    # BigQuery target (production path).
    gcp_project: str = ""
    bq_dataset: str = "secure_views"
    bq_location: str = "US"

    # Vertex AI (production path).
    vertex_project: str = ""
    vertex_location: str = "us-central1"
    vertex_model: str = "gemini-2.5-pro"

    # Google AI Studio (free local testing path, no GCP project needed).
    gemini_api_key: str = ""
    aistudio_model: str = "gemini-2.5-flash"

    # Local demo data (DuckDB executor).
    data_dir: Path = _DEFAULT_DATA_DIR

    # Guardrail limits.
    max_rows: int = 1000
    max_bytes_billed: int = _DEFAULT_MAX_BYTES_BILLED

    @property
    def logical_dataset(self) -> str:
        """Dataset name used to qualify tables in generated SQL."""
        return self.bq_dataset


def load_settings() -> Settings:
    """Build settings from the current environment."""
    gcp_project = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    return Settings(
        provider=os.getenv("NLA_PROVIDER", "mock"),
        executor=os.getenv("NLA_EXECUTOR", "duckdb"),
        gcp_project=gcp_project,
        bq_dataset=os.getenv("NLA_BQ_DATASET", "secure_views"),
        bq_location=os.getenv("NLA_BQ_LOCATION", "US"),
        vertex_project=os.getenv("NLA_VERTEX_PROJECT", gcp_project),
        vertex_location=os.getenv("NLA_VERTEX_LOCATION", "us-central1"),
        vertex_model=os.getenv("NLA_VERTEX_MODEL", "gemini-2.5-pro"),
        gemini_api_key=os.getenv("NLA_GEMINI_API_KEY", ""),
        aistudio_model=os.getenv("NLA_AISTUDIO_MODEL", "gemini-2.5-flash"),
        data_dir=Path(os.getenv("NLA_DATA_DIR", str(_DEFAULT_DATA_DIR))),
        max_rows=int(os.getenv("NLA_MAX_ROWS", "1000")),
        max_bytes_billed=int(
            os.getenv("NLA_MAX_BYTES_BILLED", str(_DEFAULT_MAX_BYTES_BILLED))
        ),
    )
