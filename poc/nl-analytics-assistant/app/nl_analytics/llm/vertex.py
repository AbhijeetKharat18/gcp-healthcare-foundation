"""Gemini-on-Vertex-AI provider (the production text->SQL backend).

Runs inside the delivery project, so model traffic stays within the VPC-SC
perimeter and is billed/audited under ``sa-delivery``. The Vertex SDK is
imported lazily (only when this provider is actually selected) so the offline
demo and tests carry no cloud dependency.
"""

from __future__ import annotations

from ._clean import clean_sql

# Deterministic generation: we want the same question to yield the same SQL.
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
        self._model = None  # built on first use

    def _get_model(self):
        if self._model is None:
            import vertexai
            from vertexai.generative_models import GenerativeModel

            vertexai.init(project=self.project, location=self.location)
            self._model = GenerativeModel(self.model_name)
        return self._model

    def generate_sql(self, question: str, system_prompt: str) -> str:
        from vertexai.generative_models import GenerationConfig

        model = self._get_model()
        prompt = f"{system_prompt}\n\nQuestion: {question}\n\nSQL:"
        response = model.generate_content(
            prompt,
            generation_config=GenerationConfig(
                temperature=_TEMPERATURE,
                max_output_tokens=_MAX_OUTPUT_TOKENS,
                candidate_count=1,
            ),
        )
        # response.text raises if the model returned no candidates or the
        # response was blocked / truncated; surface a clean message instead.
        try:
            text = response.text
        except (ValueError, AttributeError, IndexError) as exc:
            raise RuntimeError(
                "Vertex returned no usable text (response may have been blocked "
                "or truncated)."
            ) from exc
        sql = clean_sql(text)
        if not sql:
            raise RuntimeError("Vertex returned an empty response.")
        return sql
