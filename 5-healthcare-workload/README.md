# 5-healthcare-workload

The healthcare data platform deployed into the projects from stage 4, for every
environment. This is the payload that makes the foundation specifically a
*healthcare* lakehouse — it implements the inner columns of both diagrams.

## What it creates (per environment)
- **Cloud Healthcare API** (`healthcare-api.tf`): a dataset with **FHIR R4**,
  **HL7v2**, and **DICOM** stores. Each store publishes CMEK-encrypted Pub/Sub
  notifications; the FHIR store **streams into `raw_phi`** via StreamConfig.
- **BigQuery medallion lakehouse** (`lakehouse.tf`): `raw_phi`,
  `standardized_phi`, `curated_phi`, `deidentified`, `analytics_mart`,
  `secure_views` — all CMEK-encrypted with the env key.
- **GCS landing zone** (`storage.tf`): CMEK bucket for file/extract ingestion,
  30-day lifecycle expiry.
- **Cloud DLP** (`dlp.tf`): inspect + de-identify templates for PHI infoTypes.
- **Column-Level Security** (`cls-taxonomy.tf`): a Data Catalog policy-tag
  taxonomy (`phi_high`/`phi_medium`/`phi_low`) with an example fine-grained grant.
- **Secure views + RLS** (`secure-views.tf`): `secure_views` authorized to read
  `curated_phi`; an optional `SESSION_USER()` row-filtering view.
- **Workload identities** (`iam.tf`): least-privilege SAs for ingestion,
  pipeline, and delivery.

## Data flow realized
FHIR/HL7v2/DICOM stores → (FHIR StreamConfig) → `raw_phi` → *(harmonization
pipeline)* → `standardized_phi` → `curated_phi` → *(DLP)* → `deidentified` /
`analytics_mart`; governed reads via `secure_views` (CLS + RLS). Delivery SAs
read **only** `secure_views`, never raw PHI.

## Run
1. Set `bootstrap_state_bucket`, `backend.tf` bucket, and `analysts_group`.
2. `terraform init && terraform apply`

## Scope boundary (what's intentionally not here)
This stage provisions the **data-plane platform and its IAM**. The *compute*
that moves data — the GKE MLLP adapter, the Dataflow/Whistle harmonization
jobs, the Cloud Run / API Gateway delivery services — is application code +
deployment that runs on top of this. The runtime SAs and target datasets are
ready for them. Those compute resources are the natural next layer.

## Known caveats (verify with `plan`)
- **Healthcare CMEK** is not Terraform-settable; configure via the dataset
  encryptionSpec API (see note in `healthcare-api.tf` and `1-org`).
- **FHIR→BigQuery streaming** requires the destination dataset + agent grants to
  align; wired via `depends_on`, but confirm in your project.
- **Example RLS view** is off by default (`create_example_views=false`) because
  it references curated tables that don't exist in a fresh deployment.
- **Tokenization** with re-identification needs a KMS-wrapped DLP key (documented).
