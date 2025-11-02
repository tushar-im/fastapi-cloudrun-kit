output "pool_name" {
  description = "Fully-qualified name of the Workload Identity Pool."
  value       = google_iam_workload_identity_pool.pool.name
}

output "provider_name" {
  description = "Fully-qualified name of the Workload Identity Pool Provider."
  value       = google_iam_workload_identity_pool_provider.provider.name
}

output "member" {
  description = "PrincipalSet identifier used in the service account binding."
  value       = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.pool.name}/attribute.repository/${var.github_repository}"
}
