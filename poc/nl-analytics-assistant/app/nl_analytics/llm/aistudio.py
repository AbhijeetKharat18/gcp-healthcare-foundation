"""Google AI Studio (Gemini Developer API) provider.

Lets you test *real* natural-language -> SQL locally with a **free** AI Studio
API key (https://aistudio.google.com/apikey) - no GCP project, no billing, no
Vertex. It uses the same Gemini model family as the production Vertex path, so
it is the closest local stand-in.

Set NLA_PROVIDER=aistudio and NLA_GEMINI_API_KEY=<key>. The SDK is imported
lazily so the offline mock/DuckDB path and the tests carry no dependency on it.
"""

from __future__ import annotations

from ._clean import clean_sql

_TEMPERATURE = 0.0
_MAX_OUTPUT_TOKENS = 1024


class AIStudioGeminiProvider:
    name = "aistudio"

    def __init__(self, api_key: str, model: str) -> None:
        if not api_key:
            raise ValueError(
                "AI Studio provider requires an API key. Set NLA_GEMINI_API_KEY "
                "(get a free key at https://aistudio.google.com/apikey)."
            )
        self.api_key = api_key
        self.model_name = model
        self._client = None  # built on first use

    def _get_client(self):
        if self._client is None:
            from google import genai

            self._client = genai.Client(api_key=self.api_key)
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
                "AI Studio returned no usable text (response may have been "
                "blocked or truncated)."
            )
        sql = clean_sql(text)
        if not sql:
            raise RuntimeError("AI Studio returned an empty response.")
        return sql
