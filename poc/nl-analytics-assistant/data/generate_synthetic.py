#!/usr/bin/env python3
"""Generate de-identified synthetic data for the NL Analytics Assistant demo.

A deliberately small "Synthea-lite" generator: it produces rows that match the
``secure_views`` contract (see ``schema/secure_views.sql``) so the assistant can
be demoed end-to-end with **zero real PHI** and zero cloud dependencies.

Only the Python standard library is used, and the RNG is seeded, so output is
deterministic and safe to commit. Every field is already de-identified
(age_band not DOB, zip3 not ZIP+4, tokenised keys not MRNs).

Usage:
    python data/generate_synthetic.py [--out data/synthetic] [--patients 2000]
"""

from __future__ import annotations

import argparse
import csv
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 20260918
TODAY = date(2026, 9, 18)

REGIONS = ["North", "South", "East", "West", "Central"]

FACILITIES = [
    ("FAC-01", "Cedar Ridge Medical Center", "North", 420),
    ("FAC-02", "Bayview General Hospital", "West", 310),
    ("FAC-03", "Prairie Health System", "Central", 180),
    ("FAC-04", "Summit Regional Hospital", "East", 260),
    ("FAC-05", "Harbor Community Hospital", "South", 140),
]

AGE_BANDS = ["0-17", "18-34", "35-49", "50-64", "65-79", "80+"]
AGE_WEIGHTS = [12, 18, 20, 22, 20, 8]

SEX = ["F", "M", "Other", "Unknown"]
SEX_WEIGHTS = [50, 47, 2, 1]

# Primary chronic condition -> (icd10, readmission propensity, base charge).
CONDITIONS = {
    "Diabetes": ("E11.9", 0.16, 9000),
    "Hypertension": ("I10", 0.10, 6000),
    "Congestive Heart Failure": ("I50.9", 0.22, 15000),
    "COPD": ("J44.9", 0.19, 12000),
    "Chronic Kidney Disease": ("N18.9", 0.18, 13000),
    "Asthma": ("J45.909", 0.08, 5000),
    "None": ("Z00.00", 0.05, 3000),
}
CONDITION_NAMES = list(CONDITIONS)
CONDITION_WEIGHTS = [18, 24, 10, 12, 9, 12, 15]

ENCOUNTER_TYPES = ["Inpatient", "Outpatient", "Emergency"]
ENCOUNTER_WEIGHTS = [30, 55, 15]

DEPARTMENTS = [
    "Cardiology", "Pulmonology", "Nephrology", "Endocrinology",
    "General Medicine", "Emergency", "Orthopedics", "Oncology",
]

DISPOSITIONS = ["Home", "SNF", "Home Health", "Transferred", "Expired", "AMA"]
DISPOSITION_WEIGHTS = [70, 12, 8, 5, 3, 2]

# Observations: (loinc, name, unit, low, high).
OBSERVATIONS = [
    ("4548-4", "Hemoglobin A1c", "%", 4.8, 12.5),
    ("8480-6", "Systolic blood pressure", "mmHg", 95, 185),
    ("8462-4", "Diastolic blood pressure", "mmHg", 55, 110),
    ("2160-0", "Creatinine", "mg/dL", 0.6, 4.5),
    ("2339-0", "Glucose", "mg/dL", 70, 320),
    ("718-7", "Hemoglobin", "g/dL", 8.0, 17.0),
]


def weighted(rng: random.Random, choices: list, weights: list):
    return rng.choices(choices, weights=weights, k=1)[0]


def zip3_for_region(rng: random.Random, region: str) -> str:
    base = {"North": 550, "South": 300, "East": 100, "West": 900, "Central": 600}[region]
    return f"{base + rng.randint(0, 40):03d}"


def generate(out_dir: Path, n_patients: int) -> dict[str, int]:
    rng = random.Random(SEED)
    out_dir.mkdir(parents=True, exist_ok=True)

    # --- facilities --------------------------------------------------------
    with (out_dir / "v_facility_dim.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["facility_id", "facility_name", "region", "bed_count"])
        for fid, name, region, beds in FACILITIES:
            w.writerow([fid, name, region, beds])

    facility_region = {fid: region for fid, _, region, _ in FACILITIES}
    facility_ids = [f[0] for f in FACILITIES]

    # --- patients ----------------------------------------------------------
    patients = []
    with (out_dir / "v_patient_summary.csv").open("w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["patient_key", "age_band", "sex", "zip3", "region",
                    "primary_condition", "home_facility_id"])
        for i in range(n_patients):
            pkey = f"PT-{i:06d}"
            facility = weighted(rng, facility_ids, [40, 28, 12, 15, 5])
            region = facility_region[facility]
            age_band = weighted(rng, AGE_BANDS, AGE_WEIGHTS)
            sex = weighted(rng, SEX, SEX_WEIGHTS)
            primary = weighted(rng, CONDITION_NAMES, CONDITION_WEIGHTS)
            w.writerow([pkey, age_band, sex, zip3_for_region(rng, region),
                        region, primary, facility])
            patients.append((pkey, facility, region, age_band, primary))

    # --- encounters / conditions / observations ----------------------------
    enc_rows = 0
    cond_rows = 0
    obs_rows = 0
    enc_writer_fh = (out_dir / "v_encounter_facts.csv").open("w", newline="")
    cond_writer_fh = (out_dir / "v_condition_facts.csv").open("w", newline="")
    obs_writer_fh = (out_dir / "v_observation_facts.csv").open("w", newline="")
    try:
        enc_w = csv.writer(enc_writer_fh)
        enc_w.writerow(["encounter_key", "patient_key", "facility_id", "encounter_type",
                        "department", "admit_date", "discharge_date", "length_of_stay_days",
                        "drg_code", "discharge_disposition", "is_readmission_30d", "total_charges"])
        cond_w = csv.writer(cond_writer_fh)
        cond_w.writerow(["condition_key", "patient_key", "encounter_key",
                         "icd10_code", "condition_name", "onset_date"])
        obs_w = csv.writer(obs_writer_fh)
        obs_w.writerow(["observation_key", "patient_key", "encounter_key", "loinc_code",
                        "observation_name", "value_num", "unit", "observation_date"])

        enc_seq = 0
        for pkey, facility, _region, age_band, primary in patients:
            icd10, readmit_p, base_charge = CONDITIONS[primary]
            # Older / sicker patients have more encounters.
            n_enc = rng.choices([1, 2, 3, 4, 5, 6], weights=[30, 28, 18, 12, 8, 4], k=1)[0]
            if age_band in ("65-79", "80+"):
                n_enc += rng.randint(0, 2)

            last_discharge: date | None = None
            for _ in range(n_enc):
                enc_seq += 1
                ekey = f"ENC-{enc_seq:07d}"
                etype = weighted(rng, ENCOUNTER_TYPES, ENCOUNTER_WEIGHTS)
                admit = TODAY - timedelta(days=rng.randint(0, 730))

                if etype == "Inpatient":
                    los = rng.choices(range(1, 15),
                                      weights=[16, 18, 16, 12, 9, 7, 6, 5, 4, 2, 2, 1, 1, 1],
                                      k=1)[0]
                    discharge = admit + timedelta(days=los)
                    disposition = weighted(rng, DISPOSITIONS, DISPOSITION_WEIGHTS)
                    charges = base_charge + los * rng.randint(1800, 3200)
                elif etype == "Emergency":
                    los = rng.choice([0, 0, 1])
                    discharge = admit + timedelta(days=los)
                    disposition = weighted(rng, ["Home", "Transferred", "SNF", "Expired"],
                                           [80, 12, 5, 3])
                    charges = int(base_charge * 0.4) + rng.randint(500, 2500)
                else:  # Outpatient
                    los = 0
                    discharge = None
                    disposition = "Home"
                    charges = rng.randint(150, 1800)

                # 30-day readmission only meaningful for inpatient with a prior discharge.
                is_readmit = False
                if etype == "Inpatient" and last_discharge is not None:
                    gap = (admit - last_discharge).days
                    if 0 <= gap <= 30:
                        is_readmit = rng.random() < (readmit_p + 0.5)
                    else:
                        is_readmit = rng.random() < (readmit_p * 0.1)
                if discharge is not None:
                    last_discharge = discharge

                enc_w.writerow([
                    ekey, pkey, facility, etype,
                    weighted(rng, DEPARTMENTS, [16, 12, 10, 12, 20, 15, 8, 7]),
                    admit.isoformat(),
                    discharge.isoformat() if discharge else "",
                    los, f"DRG-{rng.randint(1, 999):03d}", disposition,
                    "true" if is_readmit else "false", charges,
                ])
                enc_rows += 1

                # A condition row per encounter (primary + occasional comorbidity).
                cond_rows += 1
                cond_w.writerow([f"CND-{cond_rows:07d}", pkey, ekey, icd10, primary,
                                 admit.isoformat()])
                if rng.random() < 0.3 and primary != "None":
                    como = weighted(rng, CONDITION_NAMES, CONDITION_WEIGHTS)
                    cond_rows += 1
                    cond_w.writerow([f"CND-{cond_rows:07d}", pkey, ekey,
                                     CONDITIONS[como][0], como, admit.isoformat()])

                # A couple of observations per encounter.
                for _ in range(rng.randint(1, 3)):
                    loinc, oname, unit, lo, hi = rng.choice(OBSERVATIONS)
                    obs_rows += 1
                    obs_w.writerow([
                        f"OBS-{obs_rows:08d}", pkey, ekey, loinc, oname,
                        round(rng.uniform(lo, hi), 1), unit,
                        (discharge or admit).isoformat(),
                    ])
    finally:
        enc_writer_fh.close()
        cond_writer_fh.close()
        obs_writer_fh.close()

    return {
        "facilities": len(FACILITIES),
        "patients": n_patients,
        "encounters": enc_rows,
        "conditions": cond_rows,
        "observations": obs_rows,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", default=str(Path(__file__).resolve().parent / "synthetic"))
    parser.add_argument("--patients", type=int, default=2000)
    args = parser.parse_args()

    counts = generate(Path(args.out), args.patients)
    print("Generated de-identified synthetic data:")
    for name, n in counts.items():
        print(f"  {name:>13}: {n:,}")
    print(f"  -> {args.out}")


if __name__ == "__main__":
    main()
