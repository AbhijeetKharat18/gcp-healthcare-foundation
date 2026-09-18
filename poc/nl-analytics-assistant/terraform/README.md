# Terraform: NL Analytics Assistant serving layer

Deploys the assistant as a Cloud Run service in the **delivery** project,
running as the existing `sa-delivery` identity, and grants that identity the two
capabilities it was still missing.

## What it creates

| Resource | Purpose |
|---|---|
| `google_cloud_run_v2_service.assistant` | The FastAPI service (Gemini + BigQuery), internal ingress only |
| `google_project_iam_member.delivery_vertex_user` | `sa-delivery` → `roles/aiplatform.user` on the delivery project |
| `google_project_iam_member.delivery_bq_job_user` | `sa-delivery` → `roles/bigquery.jobUser` on the lakehouse project |
| `google_service_account_iam_member.tf_can_actas_delivery` | lets the Terraform SA deploy Cloud Run *as* `sa-delivery` |
| `google_cloud_run_v2_service_iam_member.invokers` | authenticated invokers (`var.invoker_members`) |

`sa-delivery` gains **no new data-read scope** — it still reads only
`secure_views` (granted in `5-healthcare-workload/iam.tf`). It cannot see
`raw_phi`, `standardized_phi`, or `curated_phi`.

## Prerequisites

- Foundation stages `0`–`5` applied (this reads their remote state).
- An Artifact Registry repo in the delivery project, and the image built/pushed:

```bash
# from poc/nl-analytics-assistant/
REGION=us-central1
PROJECT=hcf-dev-delivery            # <prefix>-<env>-delivery
REPO=poc
gcloud artifacts repositories create $REPO --repository-format=docker \
  --location=$REGION --project=$PROJECT   # once
gcloud auth configure-docker $REGION-docker.pkg.dev
IMAGE=$REGION-docker.pkg.dev/$PROJECT/$REPO/nl-analytics:v0.1.0
docker build -t $IMAGE .
docker push $IMAGE
```

## Apply

```bash
cp backend.tf.example backend.tf                 # set your tfstate bucket
cp terraform.tfvars.example terraform.tfvars     # set container_image, invokers
terraform init
terraform plan
terraform apply
```

## Notes

- **Ingress is internal-only.** Put an internal HTTPS load balancer + IAP in
  front for human users. VPC-SC governs `sa-delivery`'s calls to Vertex and
  BigQuery by identity + perimeter (both projects are perimeter members)
  regardless of network path. For a fully private network path, add **Direct
  VPC egress** / a Serverless VPC Access connector so egress leaves via the
  restricted Google APIs VIP rather than the public internet:

  ```hcl
  # inside template { ... }
  vpc_access {
    network_interfaces {
      network    = "<host-vpc>"     # from stage 3 output
      subnetwork = "<env-subnet>"   # from stage 3 output
    }
    egress = "ALL_TRAFFIC"
  }
  ```
  Left out of the POC because it needs the connector/subnet wiring from stage 3.
- BigQuery query jobs run in the lakehouse project (where `secure_views` lives),
  so generated SQL needs no cross-project qualifier. Vertex runs in the delivery
  project.
- `terraform validate` needs no cloud access; `plan`/`apply` do (via the
  foundation's Workload Identity Federation / impersonation).
