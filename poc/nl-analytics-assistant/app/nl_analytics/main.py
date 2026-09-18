"""FastAPI entrypoint for the NL Analytics Assistant."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field

from .catalog import TABLES
from .config import load_settings
from .prompt import build_system_prompt
from .service import AnalyticsService

logging.basicConfig(level=logging.INFO)

_STATIC_DIR = Path(__file__).resolve().parent / "static"

SAMPLE_QUESTIONS = [
    "What is the 30-day readmission rate by facility?",
    "What is the average length of stay by encounter type?",
    "How many patients have diabetes by region?",
    "Which are the top 5 facilities by encounter volume?",
    "What are total charges by region?",
    "How many patients are in each age band?",
]


class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


@lru_cache(maxsize=1)
def get_service() -> AnalyticsService:
    return AnalyticsService()


app = FastAPI(
    title="NL Analytics Assistant",
    description="Governed natural-language querying of the secure_views lakehouse layer.",
    version="0.1.0",
)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    settings = load_settings()
    return {
        "status": "ok",
        "provider": settings.provider,
        "executor": settings.executor,
    }


@app.get("/api/schema")
def schema() -> dict[str, object]:
    return {
        "dataset": load_settings().logical_dataset,
        "tables": [
            {
                "name": t.name,
                "description": t.description,
                "columns": [
                    {"name": c.name, "type": c.type, "description": c.description}
                    for c in t.columns
                ],
            }
            for t in TABLES
        ],
    }


@app.get("/api/samples")
def samples() -> dict[str, list[str]]:
    return {"questions": SAMPLE_QUESTIONS}


@app.get("/api/prompt")
def prompt() -> dict[str, str]:
    """Expose the exact grounding prompt, for transparency in the demo."""
    return {"system_prompt": build_system_prompt(load_settings().logical_dataset)}


@app.post("/api/ask")
def ask(request: AskRequest) -> JSONResponse:
    result = get_service().ask(request.question)
    status = 200 if result.ok else 422
    return JSONResponse(status_code=status, content=result.to_dict())


@app.get("/")
def index() -> FileResponse:
    return FileResponse(_STATIC_DIR / "index.html")
