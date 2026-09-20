"""Ollama provider - fully offline, no API key, no GCP.

Talks to a local Ollama server (default http://localhost:11434) over its native
HTTP API, so you can test real natural-language -> SQL entirely on your own
machine with whatever model you have pulled. Set NLA_PROVIDER=ollama and
NLA_OLLAMA_MODEL to a model you have (a code/SQL-tuned model such as
qwen2.5-coder works best; general models like llama3.1 also work).

httpx is imported lazily so the mock/DuckDB path carries no dependency on it.
"""

from __future__ import annotations

from ._clean import clean_sql

_DEFAULT_TIMEOUT_S = 120.0


class OllamaProvider:
    name = "ollama"

    def __init__(self, host: str, model: str, timeout: float = _DEFAULT_TIMEOUT_S) -> None:
        self.host = (host or "http://localhost:11434").rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client = None  # built on first use

    def _get_client(self):
        if self._client is None:
            import httpx

            self._client = httpx.Client(timeout=self.timeout)
        return self._client

    def generate_sql(self, question: str, system_prompt: str) -> str:
        client = self._get_client()
        payload = {
            "model": self.model,
            "system": system_prompt,
            "prompt": f"Question: {question}\n\nSQL:",
            "stream": False,
            "options": {"temperature": 0},
        }
        try:
            response = client.post(f"{self.host}/api/generate", json=payload)
            response.raise_for_status()
        except Exception as exc:
            raise RuntimeError(
                f"Could not reach Ollama at {self.host} (is it running, and is "
                f"model {self.model!r} pulled?): {exc}"
            ) from exc

        text = response.json().get("response", "")
        sql = clean_sql(text)
        if not sql:
            raise RuntimeError("Ollama returned an empty response.")
        return sql
