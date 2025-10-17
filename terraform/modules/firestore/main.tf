resource "google_firestore_database" "database" {
  project     = var.project_id
  name        = var.database_name
  location_id = var.location_id
  type        = "FIRESTORE_NATIVE"

  # The labels field is not available for this resource.
  # We can't add labels here directly.
}
