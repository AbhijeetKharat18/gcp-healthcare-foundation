-- ---------------------------------------------------------------------------
-- secure_views schema (the governed contract for the NL Analytics Assistant)
-- ---------------------------------------------------------------------------
-- These are the ONLY objects the assistant is allowed to query. They live in
-- the lakehouse project's `secure_views` dataset (created in
-- 5-healthcare-workload/lakehouse.tf) and are read by `sa-delivery`, which has
-- no access to raw_phi / standardized_phi / curated_phi.
--
-- Governance built into the contract:
--   * No direct identifiers. No name, MRN, SSN, full DOB, phone, email, or
--     street address is ever exposed here.
--   * Quasi-identifiers are generalised: age_band (not DOB), zip3 (not ZIP+4),
--     dates truncated to the day. This is what the `deidentified` / CLS layer
--     produces before it is surfaced as a view.
--   * Row-level security is applied by the view itself (see the RLS pattern in
--     5-healthcare-workload/secure-views.tf); the assistant inherits it.
--
-- In BigQuery these are VIEWS over curated_phi. For the local demo they are
-- materialised as DuckDB tables of the same name and shape. The column set and
-- descriptions below are the single source of truth mirrored in
-- app/nl_analytics/catalog.py.
-- ---------------------------------------------------------------------------

-- Facility dimension --------------------------------------------------------
CREATE OR REPLACE VIEW `secure_views.v_facility_dim` AS
SELECT
  facility_id,          -- STRING  Stable facility identifier (e.g. 'FAC-01')
  facility_name,        -- STRING  Human-readable facility name
  region,               -- STRING  Geographic region grouping
  bed_count             -- INT64   Licensed bed count
FROM `curated_phi.facility`;

-- Patient summary (de-identified, one row per patient) ----------------------
CREATE OR REPLACE VIEW `secure_views.v_patient_summary` AS
SELECT
  patient_key,          -- STRING  Tokenised surrogate key (NOT an MRN)
  age_band,             -- STRING  '0-17','18-34','35-49','50-64','65-79','80+'
  sex,                  -- STRING  'F','M','Other','Unknown'
  zip3,                 -- STRING  First 3 digits of postal code
  region,               -- STRING  Geographic region
  primary_condition,    -- STRING  Primary chronic condition label
  home_facility_id      -- STRING  Facility the patient is primarily seen at
FROM `curated_phi.patient`;

-- Encounter facts -----------------------------------------------------------
CREATE OR REPLACE VIEW `secure_views.v_encounter_facts` AS
SELECT
  encounter_key,        -- STRING   Surrogate encounter key
  patient_key,          -- STRING   FK -> v_patient_summary.patient_key
  facility_id,          -- STRING   FK -> v_facility_dim.facility_id
  encounter_type,       -- STRING   'Inpatient','Outpatient','Emergency'
  department,           -- STRING   Clinical department / service line
  admit_date,           -- DATE     Admission / encounter start date
  discharge_date,       -- DATE     Discharge date (NULL if outpatient)
  length_of_stay_days,  -- INT64    Discharge - admit, in days (0 for same-day)
  drg_code,             -- STRING   Diagnosis-related group code
  discharge_disposition,-- STRING   'Home','SNF','Expired','Transferred', etc.
  is_readmission_30d,   -- BOOL     TRUE if within 30d of a prior discharge
  total_charges         -- NUMERIC  Total billed charges for the encounter (USD)
FROM `curated_phi.encounter`;

-- Condition facts -----------------------------------------------------------
CREATE OR REPLACE VIEW `secure_views.v_condition_facts` AS
SELECT
  condition_key,        -- STRING  Surrogate condition key
  patient_key,          -- STRING  FK -> v_patient_summary.patient_key
  encounter_key,        -- STRING  FK -> v_encounter_facts.encounter_key
  icd10_code,           -- STRING  ICD-10-CM code
  condition_name,       -- STRING  Human-readable condition label
  onset_date            -- DATE    Recorded onset date
FROM `curated_phi.condition`;

-- Observation facts (labs / vitals) -----------------------------------------
CREATE OR REPLACE VIEW `secure_views.v_observation_facts` AS
SELECT
  observation_key,      -- STRING   Surrogate observation key
  patient_key,          -- STRING   FK -> v_patient_summary.patient_key
  encounter_key,        -- STRING   FK -> v_encounter_facts.encounter_key
  loinc_code,           -- STRING   LOINC code for the observation
  observation_name,     -- STRING   Human-readable observation label
  value_num,            -- FLOAT64  Numeric result value
  unit,                 -- STRING   Unit of measure
  observation_date      -- DATE     Date the observation was taken
FROM `curated_phi.observation`;
