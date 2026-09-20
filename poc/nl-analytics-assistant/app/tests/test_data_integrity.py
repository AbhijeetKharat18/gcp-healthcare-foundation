"""Integrity + de-identification checks on the synthetic secure_views data.

Validates that the generated CSVs honour the governed contract: referential
integrity across the tables, valid domains, and - critically - that no direct
identifier ever appears in the data a user (or the assistant) can reach.
"""

from __future__ import annotations

import csv

import pytest
from nl_analytics.config import load_settings

DATA_DIR = load_settings().data_dir

# Substrings that would indicate a direct identifier leaked into the data.
FORBIDDEN_COLUMN_TOKENS = [
    "name", "ssn", "dob", "birth", "mrn", "phone", "email", "address", "street",
]
# patient_key / encounter_key etc. are surrogate keys; "name" only appears in
# facility_name, which is not a patient identifier - allow that one explicitly.
ALLOWED_NAME_COLUMNS = {"facility_name", "condition_name", "observation_name"}

AGE_BANDS = {"0-17", "18-34", "35-49", "50-64", "65-79", "80+"}


def _rows(table: str) -> list[dict]:
    with (DATA_DIR / f"{table}.csv").open() as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def data():
    return {
        t: _rows(t)
        for t in [
            "v_facility_dim", "v_patient_summary", "v_encounter_facts",
            "v_condition_facts", "v_observation_facts",
        ]
    }


def test_all_tables_have_rows(data):
    for table, rows in data.items():
        assert rows, f"{table} is empty"


def test_no_direct_identifier_columns(data):
    for table, rows in data.items():
        columns = rows[0].keys()
        for col in columns:
            if col in ALLOWED_NAME_COLUMNS:
                continue
            low = col.lower()
            assert not any(tok in low for tok in FORBIDDEN_COLUMN_TOKENS), (
                f"{table}.{col} looks like a direct identifier"
            )


def test_patient_keys_unique(data):
    keys = [r["patient_key"] for r in data["v_patient_summary"]]
    assert len(keys) == len(set(keys))


def test_age_bands_valid(data):
    assert {r["age_band"] for r in data["v_patient_summary"]} <= AGE_BANDS


def test_encounter_referential_integrity(data):
    patients = {r["patient_key"] for r in data["v_patient_summary"]}
    facilities = {r["facility_id"] for r in data["v_facility_dim"]}
    for e in data["v_encounter_facts"]:
        assert e["patient_key"] in patients
        assert e["facility_id"] in facilities


def test_condition_and_observation_integrity(data):
    patients = {r["patient_key"] for r in data["v_patient_summary"]}
    encounters = {r["encounter_key"] for r in data["v_encounter_facts"]}
    for c in data["v_condition_facts"]:
        assert c["patient_key"] in patients
        assert c["encounter_key"] in encounters
    for o in data["v_observation_facts"]:
        assert o["patient_key"] in patients
        assert o["encounter_key"] in encounters


def test_readmission_flag_only_for_inpatient(data):
    for e in data["v_encounter_facts"]:
        if e["is_readmission_30d"] == "true":
            assert e["encounter_type"] == "Inpatient"


def test_length_of_stay_non_negative(data):
    for e in data["v_encounter_facts"]:
        assert int(e["length_of_stay_days"]) >= 0
