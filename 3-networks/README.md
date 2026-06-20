# 3-networks

Per-environment Shared VPC networking and the VPC Service Controls perimeters.
This is the dotted "VPC-SC perimeter" boundary and the private connectivity in
both architecture diagrams.

## What it creates (per environment, via `modules/net-env`)
- **Shared VPC host project** (`hcf-<env>-net`) with a custom-mode VPC.
- **Primary subnet** with **Private Google Access** + secondary ranges
  (`pods`, `services`) for GKE, and VPC flow logs.
- **Firewall:** allow internal, IAP (`35.235.240.0/20`), Google health-check
  ranges; **egress lockdown** — allow only internal + the restricted Google
  APIs VIP, deny all other egress.
- **Cloud NAT** for controlled egress (VMs have no external IPs by org policy).
- **Private DNS** mapping `*.googleapis.com` → `restricted.googleapis.com`
  (`199.36.153.4/30`), keeping API traffic on Google's backbone and inside the
  perimeter.

## VPC Service Controls (`vpc-sc.tf`)
- One **org access policy** + a **`trusted` access level** (corporate IP ranges).
- One **REGULAR service perimeter per environment**, restricting Healthcare,
  BigQuery, Storage, Pub/Sub, DLP, KMS, and Vertex AI.
- Perimeters start **empty**; stage 4 adds each workload project as it's
  created. `lifecycle.ignore_changes` on `resources` lets stage 4 own
  membership without Terraform thrashing.

## Run
1. Set `bootstrap_state_bucket`, the `backend.tf` bucket, and **real
   `trusted_ip_ranges`**.
2. `terraform init && terraform apply`

## Outputs (downstream)
`networks` (per-env host project / network / subnet), `access_policy_name`,
`perimeter_names`.

## Caveats to verify
- **One org-scoped access policy per org**: if your org already has one, import
  it instead of creating a second.
- **Egress deny-all is opinionated.** It's the right posture for PHI but will
  block outbound internet (e.g., public package mirrors). Pull dependencies via
  Artifact Registry / restricted VIP, or add scoped allow rules.
- CIDR ranges in `cidr_plan` are non-overlapping across envs; adjust to your IPAM.
