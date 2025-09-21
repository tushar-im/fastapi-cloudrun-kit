resource "google_artifact_registry_repository" "repository" {
  project       = var.project_id
  location      = var.region
  repository_id = var.repository
  description   = "Docker repository for ${var.repository} images"
  format        = "DOCKER"
  labels        = var.labels
}
