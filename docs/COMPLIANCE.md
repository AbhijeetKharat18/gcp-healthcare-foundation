# Compliance Control Mapping

How this codebase implements the controls in the two architecture diagrams.
Terraform enforces the **technical** safeguards; the **process** items (OIG
seven elements, Texas HB 300 SLAs) are organizational and are mapped to the
technical control that *supports* them, not enforced by code.

> Reference scope: greenfield, placeholder values. This is a control map, not a
> certification. Validate against your own risk assessment and a HIPAA BAA.

## Technical safeguards (enforced in Terraform)

| Control | Where | Stage |
|---|---|---|
| Encryption at rest (CMEK) | KMS keys + `default_kms_key_name` / `kms_key_name` on state, logs, BQ, GCS, Pub/Sub | 0,1,2,5 |
| CMEK required org-wide | `gcp.restrictNonCmekServices` org policy | 1 |
| Encryption in transit | Restricted Google APIs VIP + private DNS; TLS to GCP APIs | 3 |
| Access control / least privilege | Impersonated foundation SA; per-workload SAs with scoped roles; no SA keys | 0,1,5 |
| Network isolation / exfiltration | Shared VPC, egress lockdown, **VPC-SC perimeters** | 3,4 |
| Audit controls | Org-aggregated audit sink → **immutable (bucket-locked)** archive | 1 |
| Threat detection & response | SCC findings → Pub/Sub; Essential Contacts | 1 |
| Data residency | `gcp.resourceLocations` org policy | 1 |
| De-identification of PHI | DLP inspect + de-identify templates | 5 |
| Column-level security | Data Catalog policy-tag taxonomy + fine-grained reader | 5 |
| Row-level security | Authorized `secure_views` + `SESSION_USER()` filtering | 5 |
| Least-exposure delivery | Delivery SAs read `secure_views` only | 5 |

## HIPAA Security Rule (diagram Image 2)

| Rule | Supported by |
|---|---|
| Access Control | VPC-SC, IAM least privilege, IAP, OS Login |
| Audit Controls | Immutable org audit sink + flow logs |
| Integrity / de-id | DLP de-identify templates; FHIR store integrity settings |
| Person/Entity Authentication | Impersonation + group-based IAM (wire to your IdP/MFA) |
| Transmission Security | Restricted VIP, TLS, egress lockdown |

## OIG Seven Elements (diagram Image 1) — process mapped to technical anchor

| Element | Technical anchor (this repo) | Process owner |
|---|---|---|
| 1 Policies & standards | Org policies, this control map | Compliance team |
| 2 Leadership & oversight | Billing budgets, SCC dashboards | Platform owner |
| 3 Training & education | — | HR / Compliance |
| 4 Lines of communication | SCC → Pub/Sub, Essential Contacts | SecOps |
| 5 Internal monitoring & auditing | Audit sink, flow logs, DLP findings | SecOps |
| 6 Enforcement of standards | Org policies, CLS/RLS, IAM | Platform |
| 7 Response to detected offenses | SCC findings pipeline (wire to SIEM/playbooks) | IR team |

## Texas HB 300 (diagram Image 1) — mapping

| Requirement | Anchor / note |
|---|---|
| 15 business-day EHR access | Application SLA on delivery APIs (not infra-enforced) |
| Training within 90 days | Process; tracked outside Terraform |
| Breach notice threshold 250+ | IR process; SCC pipeline feeds detection |
| Applies to TX residents' PHI regardless of org location | Data residency policy + de-id reduce scope |

## Honest limitations
- Healthcare API CMEK is configured outside Terraform (provider gap).
- MFA / IdP federation is assumed at the Google Workspace / Cloud Identity layer.
- BigQuery native row access policies have no Terraform resource yet; RLS here
  uses authorized views (`SESSION_USER()`), a common and supported alternative.
- Process controls (training, breach notification, SLAs) are organizational.
