resource "google_service_account" "service_account" {
  project      = var.project_id
  account_id   = var.name
  display_name = "Service Account for ${var.name}"
  description  = "A service account for the FastAPI Cloud Run service and associated resources."
}

# Core roles required for the service to run
resource "google_project_iam_member" "core_roles" {
  for_each = toset([
    "roles/run.admin",
    "roles/iam.serviceAccountUser",
    "roles/secretmanager.secretAccessor",
    "roles/datastore.user", # For Firestore
  ])

  project = var.project_id
  role    = each.key
  member  = google_service_account.service_account.member
}

# Optional role for reading from Artifact Registry
resource "google_project_iam_member" "artifact_registry_reader" {
  count = var.enable_artifact_registry_reader ? 1 : 0

  project = var.project_id
  role    = "roles/artifactregistry.reader"
  member  = google_service_account.service_account.member
}

# Optional role for Cloud Scheduler to create OIDC tokens
resource "google_project_iam_member" "scheduler_token_creator" {
  count = var.enable_scheduler_token_creator ? 1 : 0

  project = var.project_id
  role    = "roles/iam.serviceAccountTokenCreator"
  member  = google_service_account.service_account.member
}
