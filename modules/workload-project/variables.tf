# modules/workload-project/variables.tf
variable "prefix"          { type = string }
variable "env_short"       { type = string }
variable "component"       { type = string }
variable "folder_id"       { type = string }
variable "billing_account" { type = string }
variable "host_project_id" { type = string }
variable "region"          { type = string }
variable "subnet_name"     { type = string }
variable "apis"            { type = list(string) }
