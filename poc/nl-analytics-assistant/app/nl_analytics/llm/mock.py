"""Deterministic offline provider for the local demo and tests.

It maps a question to a canned BigQuery query using simple keyword matching.
This lets the whole pipeline (grounding -> generation -> guardrails ->
execution -> answer) run with no cloud calls, and gives the test suite a stable
oracle. It intentionally emits real BigQuery Standard SQL so it exercises the
same guardrail and transpilation path as the Vertex provider.
"""

from __future__ import annotations

import re

_DS = "secure_views"

# (keywords_all_present, sql) - first match wins.
_RULES: list[tuple[tuple[str, ...], str]] = [
    (
        ("readmission", "facility"),
        f"""
        SELECT f.facility_name,
               COUNTIF(e.is_readmission_30d) AS readmissions,
               COUNT(*) AS inpatient_encounters,
               ROUND(SAFE_DIVIDE(COUNTIF(e.is_readmission_30d), COUNT(*)) * 100, 1)
                 AS readmission_rate_pct
        FROM {_DS}.v_encounter_facts AS e
        JOIN {_DS}.v_facility_dim AS f USING (facility_id)
        WHERE e.encounter_type = 'Inpatient'
        GROUP BY f.facility_name
        ORDER BY readmission_rate_pct DESC
        """,
    ),
    (
        ("readmission",),
        f"""
        SELECT ROUND(SAFE_DIVIDE(COUNTIF(is_readmission_30d), COUNT(*)) * 100, 1)
                 AS readmission_rate_pct,
               COUNT(*) AS inpatient_encounters
        FROM {_DS}.v_encounter_facts
        WHERE encounter_type = 'Inpatient'
        """,
    ),
    (
        ("length", "stay"),
        f"""
        SELECT encounter_type,
               ROUND(AVG(length_of_stay_days), 2) AS avg_length_of_stay_days,
               COUNT(*) AS encounters
        FROM {_DS}.v_encounter_facts
        GROUP BY encounter_type
        ORDER BY avg_length_of_stay_days DESC
        """,
    ),
    (
        ("charges", "region"),
        f"""
        SELECT f.region,
               ROUND(SUM(e.total_charges), 0) AS total_charges,
               ROUND(AVG(e.total_charges), 0) AS avg_charge_per_encounter
        FROM {_DS}.v_encounter_facts AS e
        JOIN {_DS}.v_facility_dim AS f USING (facility_id)
        GROUP BY f.region
        ORDER BY total_charges DESC
        """,
    ),
    (
        ("diabetes", "region"),
        f"""
        SELECT region, COUNT(*) AS patients
        FROM {_DS}.v_patient_summary
        WHERE primary_condition = 'Diabetes'
        GROUP BY region
        ORDER BY patients DESC
        """,
    ),
    (
        ("age",),
        f"""
        SELECT age_band, COUNT(*) AS patients
        FROM {_DS}.v_patient_summary
        GROUP BY age_band
        ORDER BY age_band
        """,
    ),
    (
        ("volume",),
        f"""
        SELECT f.facility_name, COUNT(*) AS encounters
        FROM {_DS}.v_encounter_facts AS e
        JOIN {_DS}.v_facility_dim AS f USING (facility_id)
        GROUP BY f.facility_name
        ORDER BY encounters DESC
        LIMIT 5
        """,
    ),
    (
        ("condition",),
        f"""
        SELECT primary_condition, COUNT(*) AS patients
        FROM {_DS}.v_patient_summary
        GROUP BY primary_condition
        ORDER BY patients DESC
        """,
    ),
]

_FALLBACK = f"""
SELECT encounter_type, COUNT(*) AS encounters
FROM {_DS}.v_encounter_facts
GROUP BY encounter_type
ORDER BY encounters DESC
"""

# Simulated *unsafe* generations. A well-behaved model would not emit these, but
# to prove the guardrails offline (no live model, no real jailbreak needed) the
# mock deliberately produces out-of-scope / destructive SQL for adversarial
# trigger phrases. Each is designed to be caught by guardrails.enforce().
_ADVERSARIAL: list[tuple[tuple[str, ...], str]] = [
    (("curated_phi",), "SELECT * FROM curated_phi.patient"),
    (("raw_phi",), "SELECT * FROM raw_phi.patient"),
    (("delete",), f"DELETE FROM {_DS}.v_encounter_facts"),
    (("drop",), f"DROP TABLE {_DS}.v_patient_summary"),
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


class MockProvider:
    name = "mock"

    def generate_sql(self, question: str, system_prompt: str) -> str:  # noqa: ARG002
        q = _norm(question)
        for keywords, sql in _ADVERSARIAL:
            if all(k in q for k in keywords):
                return sql
        for keywords, sql in _RULES:
            if all(k in q for k in keywords):
                return _dedent(sql)
        return _dedent(_FALLBACK)


def _dedent(sql: str) -> str:
    return "\n".join(line.strip() for line in sql.strip().splitlines())
