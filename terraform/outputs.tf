output "CLOUD_RUN_URL" {
  description = "The URL of the deployed Cloud Run service."
  value       = module.cloud_run.url
}

output "CLOUD_RUN_SERVICE_ACCOUNT" {
  description = "Service account email used by Cloud Run (store as GitHub secret)."
  value       = module.service_account.email
}

output "GCP_PROJECT_ID" {
  description = "Project ID for this deployment (store as GitHub secret)."
  value       = var.project_id
}

output "CLOUD_RUN_REGION" {
  description = "Region of the Cloud Run service (store as GitHub secret)."
  value       = var.region
}

output "CLOUD_RUN_SERVICE_NAME" {
  description = "Cloud Run service name (store as GitHub secret)."
  value       = var.service_name
}

output "GCP_WORKLOAD_IDENTITY_PROVIDER" {
  description = "Fully-qualified Workload Identity Provider resource name (store as GitHub secret)."
  value       = try(module.workload_identity[0].provider_name, null)
}

output "ARTIFACT_REGISTRY_REPOSITORY" {
  description = "Artifact Registry repository URL for pushing images (store as GitHub secret)."
  value       = try(module.artifact_registry[0].repository_url, null)
}

output "SECRET_MANAGER_IDS" {
  description = "IDs of the created secrets in Secret Manager."
  value       = module.secrets.secret_ids
  sensitive   = true
}

output "FIRESTORE_DATABASE_ID" {
  description = "The ID of the Firestore database."
  value       = module.firestore.database_id
}
