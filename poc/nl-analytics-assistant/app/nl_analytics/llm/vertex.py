"""Gemini-on-Vertex-AI provider (the production text->SQL backend).

Runs inside the delivery project, so model traffic stays within the VPC-SC
perimeter and is billed/audited under ``sa-delivery``. Uses the ``google-genai``
SDK in Vertex mode (``vertexai=True``) - the supported path going forward - with
credentials resolved from the runtime service account (ADC). The SDK is imported
lazily so the offline demo and tests carry no dependency on it.
"""

from __future__ import annotations

from ._clean import clean_sql

_TEMPERATURE = 0.0
_MAX_OUTPUT_TOKENS = 1024


class VertexGeminiProvider:
    name = "vertex"

    def __init__(self, project: str, location: str, model: str) -> None:
        if not project:
            raise ValueError(
                "Vertex provider requires a project. Set NLA_VERTEX_PROJECT or "
                "GOOGLE_CLOUD_PROJECT."
            )
        self.project = project
        self.location = location
        self.model_name = model
        self._client = None  # built on first use

    def _get_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(
                vertexai=True, project=self.project, location=self.location
            )
        return self._client

    def generate_sql(self, question: str, system_prompt: str) -> str:
        from google.genai import types

        client = self._get_client()
        prompt = f"{system_prompt}\n\nQuestion: {question}\n\nSQL:"
        response = client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=_TEMPERATURE,
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                candidate_count=1,
            ),
        )
        text = getattr(response, "text", None)
        if not text:
            raise RuntimeError(
                "Vertex returned no usable text (response may have been blocked "
                "or truncated)."
            )
        sql = clean_sql(text)
        if not sql:
            raise RuntimeError("Vertex returned an empty response.")
        return sql
