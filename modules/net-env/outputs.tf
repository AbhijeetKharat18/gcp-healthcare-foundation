# modules/net-env/outputs.tf
output "host_project_id" { value = google_project.host.project_id }
output "network_id"      { value = google_compute_network.vpc.id }
output "network_name"    { value = google_compute_network.vpc.name }
output "subnet_id"       { value = google_compute_subnetwork.primary.id }
output "subnet_name"     { value = google_compute_subnetwork.primary.name }
