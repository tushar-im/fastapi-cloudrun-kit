resource "google_iam_workload_identity_pool" "pool" {
  provider = google-beta

  project                   = var.project_id
  workload_identity_pool_id = var.pool_id
  display_name              = var.pool_display_name
  description               = var.pool_description
}

resource "google_iam_workload_identity_pool_provider" "provider" {
  provider = google-beta

  project                            = var.project_id
  workload_identity_pool_id          = google_iam_workload_identity_pool.pool.workload_identity_pool_id
  workload_identity_pool_provider_id = var.provider_id
  display_name                       = var.provider_display_name
  description                        = var.provider_description
  attribute_condition                = var.attribute_condition != null ? var.attribute_condition : null

  attribute_mapping = merge(
    {
      "google.subject"       = "assertion.sub"
      "attribute.sub"        = "assertion.sub"
      "attribute.actor"      = "assertion.actor"
      "attribute.repository" = "assertion.repository"
    },
    var.attribute_mapping_overrides,
  )

  oidc {
    issuer_uri        = "https://token.actions.githubusercontent.com"
    allowed_audiences = var.allowed_audiences
  }
}

resource "google_service_account_iam_member" "wif_binding" {
  provider = google-beta

  service_account_id = "projects/${var.project_id}/serviceAccounts/${var.service_account_email}"
  role               = "roles/iam.workloadIdentityUser"
  member             = "principalSet://iam.googleapis.com/${google_iam_workload_identity_pool.pool.name}/attribute.repository/${var.github_repository}"
}
