output "repository_id" {
  description = "Artifact Registry repository ID."
  value       = google_artifact_registry_repository.repository.repository_id
}

output "repository_location" {
  description = "Region of the Artifact Registry repository."
  value       = google_artifact_registry_repository.repository.location
}

output "repository_url" {
  description = "Docker repository URL (LOCATION-docker.pkg.dev/PROJECT/REPOSITORY)."
  value       = "${google_artifact_registry_repository.repository.location}-docker.pkg.dev/${google_artifact_registry_repository.repository.project}/${google_artifact_registry_repository.repository.repository_id}"
}
