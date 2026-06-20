# 4-projects

The project factory. Builds the workload projects for every environment and
joins them to the right Shared VPC and VPC-SC perimeter.

## What it creates
For each environment (`dev`/`nonprod`/`prod`) × each component:

| Component | Maps to diagram column | Key APIs |
|---|---|---|
| `ingestion` | Secure Ingestion Layer | GKE, Pub/Sub, GCS, Dataflow |
| `healthcare-core` | Cloud Healthcare API stores | Healthcare, Pub/Sub, KMS |
| `lakehouse` | BigQuery medallion + DLP | BigQuery, DLP, Data Catalog, KMS |
| `delivery` | Looker / Vertex / APIs | Cloud Run, API Gateway, Vertex |

That's 4 projects × 3 envs = **12 workload projects**, each:
- created in its environment folder,
- **attached as a Shared VPC service project** to that env's host project,
- granted **subnet usage** (`compute.networkUser`) for its builder identities,
- **added to its environment's VPC-SC perimeter**.

## How the matrix is built
`main.tf` flattens `{env} × {component}` into one map (keys like
`dev-lakehouse`) and drives a single `for_each` over the
`modules/workload-project` module — so adding a component or environment is a
one-line change, not new copy-pasted blocks.

## Run
1. Set `bootstrap_state_bucket` + `backend.tf` bucket.
2. `terraform init && terraform apply`

## Outputs (downstream)
`projects` — nested map `env_short -> component -> { project_id, project_number }`,
consumed by stage 5 to deploy the healthcare workload.

## Notes
- Perimeter membership is added here (not in stage 3) because project numbers
  only exist once projects are created. Stage 3 left `resources` under
  `ignore_changes` precisely so this stage can own membership.
- GKE in `ingestion` may additionally need the container-engine robot granted
  `compute.networkUser` + `compute.hostServiceAgentUser`; that grant lives with
  the GKE cluster in stage 5 so it's co-located with what needs it.
