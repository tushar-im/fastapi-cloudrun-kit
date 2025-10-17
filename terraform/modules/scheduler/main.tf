resource "google_cloud_scheduler_job" "job" {
  project  = var.project_id
  region   = var.region
  name     = var.name
  schedule = var.schedule

  http_target {
    http_method = "GET"
    uri         = var.http_target_url

    oidc_token {
      service_account_email = var.service_account_email
    }
  }

  labels = var.labels
}
