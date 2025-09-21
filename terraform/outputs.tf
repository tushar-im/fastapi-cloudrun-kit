output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service."
  value       = module.cloud_run.url
}

output "service_account_email" {
  description = "The email of the created service account."
  value       = module.service_account.email
}

output "secrets_ids" {
  description = "The IDs of the created secrets in Secret Manager."
  value       = module.secrets.secret_ids
  sensitive   = true
}

output "firestore_database_id" {
  description = "The ID of the Firestore database."
  value       = module.firestore.database_id
}

output "artifact_registry_url" {
  description = "The URL of the Artifact Registry repository, if created."
  value       = var.create_artifact_registry ? module.artifact_registry[0].repository_url : "Not created"
}
