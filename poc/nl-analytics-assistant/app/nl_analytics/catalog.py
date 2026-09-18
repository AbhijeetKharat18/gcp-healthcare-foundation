"""The governed data catalog for the NL Analytics Assistant.

This module is the single source of truth for the ``secure_views`` schema that
the assistant is allowed to query. It mirrors ``data/schema/secure_views.sql``.

It drives three things:

* **Prompt grounding** - the LLM is told exactly these tables and columns.
* **Guardrail allowlist** - only these table names may appear in generated SQL.
* **Local demo** - the DuckDB executor materialises tables of this shape.

Keeping raw_phi / standardized_phi / curated_phi *out* of this catalog is
deliberate: the assistant must never be able to name them, which is a second
line of defence on top of the ``sa-delivery`` IAM grant (secure_views only).
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Column:
    name: str
    type: str
    description: str


@dataclass(frozen=True)
class Table:
    name: str
    description: str
    columns: list[Column] = field(default_factory=list)


# ---------------------------------------------------------------------------
# The governed views. Types use BigQuery Standard SQL type names; the DuckDB
# executor maps them to local equivalents.
# ---------------------------------------------------------------------------
TABLES: list[Table] = [
    Table(
        name="v_facility_dim",
        description="One row per care facility.",
        columns=[
            Column("facility_id", "STRING", "Stable facility identifier, e.g. 'FAC-01'."),
            Column("facility_name", "STRING", "Human-readable facility name."),
            Column("region", "STRING", "Geographic region grouping."),
            Column("bed_count", "INT64", "Licensed bed count."),
        ],
    ),
    Table(
        name="v_patient_summary",
        description="One de-identified row per patient. No direct identifiers.",
        columns=[
            Column("patient_key", "STRING", "Tokenised surrogate patient key (NOT an MRN)."),
            Column("age_band", "STRING", "Age band: '0-17','18-34','35-49','50-64','65-79','80+'."),
            Column("sex", "STRING", "'F','M','Other','Unknown'."),
            Column("zip3", "STRING", "First three digits of postal code."),
            Column("region", "STRING", "Geographic region."),
            Column("primary_condition", "STRING", "Primary chronic condition label."),
            Column("home_facility_id", "STRING", "Facility the patient is primarily seen at."),
        ],
    ),
    Table(
        name="v_encounter_facts",
        description="One row per encounter (visit / admission).",
        columns=[
            Column("encounter_key", "STRING", "Surrogate encounter key."),
            Column("patient_key", "STRING", "Foreign key to v_patient_summary.patient_key."),
            Column("facility_id", "STRING", "Foreign key to v_facility_dim.facility_id."),
            Column("encounter_type", "STRING", "'Inpatient','Outpatient','Emergency'."),
            Column("department", "STRING", "Clinical department / service line."),
            Column("admit_date", "DATE", "Admission / encounter start date."),
            Column("discharge_date", "DATE", "Discharge date; NULL for outpatient."),
            Column("length_of_stay_days", "INT64", "Discharge minus admit, in days."),
            Column("drg_code", "STRING", "Diagnosis-related group code."),
            Column("discharge_disposition", "STRING", "'Home','SNF','Expired','Transferred', etc."),
            Column("is_readmission_30d", "BOOL", "TRUE if within 30 days of a prior discharge."),
            Column("total_charges", "NUMERIC", "Total billed charges for the encounter, USD."),
        ],
    ),
    Table(
        name="v_condition_facts",
        description="One row per recorded condition/diagnosis.",
        columns=[
            Column("condition_key", "STRING", "Surrogate condition key."),
            Column("patient_key", "STRING", "Foreign key to v_patient_summary.patient_key."),
            Column("encounter_key", "STRING", "Foreign key to v_encounter_facts.encounter_key."),
            Column("icd10_code", "STRING", "ICD-10-CM code."),
            Column("condition_name", "STRING", "Human-readable condition label."),
            Column("onset_date", "DATE", "Recorded onset date."),
        ],
    ),
    Table(
        name="v_observation_facts",
        description="One row per observation (lab result / vital sign).",
        columns=[
            Column("observation_key", "STRING", "Surrogate observation key."),
            Column("patient_key", "STRING", "Foreign key to v_patient_summary.patient_key."),
            Column("encounter_key", "STRING", "Foreign key to v_encounter_facts.encounter_key."),
            Column("loinc_code", "STRING", "LOINC code for the observation."),
            Column("observation_name", "STRING", "Human-readable observation label."),
            Column("value_num", "FLOAT64", "Numeric result value."),
            Column("unit", "STRING", "Unit of measure."),
            Column("observation_date", "DATE", "Date the observation was taken."),
        ],
    ),
]

# Fast lookups.
TABLES_BY_NAME: dict[str, Table] = {t.name: t for t in TABLES}

# The guardrail allowlist: the only table names allowed in generated SQL.
ALLOWED_TABLES: frozenset[str] = frozenset(TABLES_BY_NAME)


def schema_prompt(dataset: str = "secure_views") -> str:
    """Render the catalog as compact text for grounding the LLM."""
    lines: list[str] = []
    for table in TABLES:
        lines.append(f"TABLE {dataset}.{table.name} -- {table.description}")
        for col in table.columns:
            lines.append(f"    {col.name} {col.type} -- {col.description}")
        lines.append("")
    return "\n".join(lines).strip()
