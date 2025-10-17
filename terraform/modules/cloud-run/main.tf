resource "google_cloud_run_v2_service" "default" {
  provider = google-beta

  name     = var.service_name
  location = var.region
  project  = var.project_id

  launch_stage = "GA"

  template {
    service_account       = var.service_account_email
    timeout               = "${var.timeout_seconds}s"
    container_concurrency = var.concurrency

    annotations = {
      "run.googleapis.com/cpu-throttling" = false
    }

    scaling {
      min_instance_count = var.min_instances
      max_instance_count = var.max_instances
    }

    containers {
      image = var.image

      resources {
        limits = {
          cpu    = var.cpu
          memory = var.memory
        }
      }

      ports {
        container_port = var.container_port
      }

      dynamic "env" {
        for_each = var.env
        content {
          name  = env.key
          value = env.value
        }
      }

      dynamic "env" {
        for_each = var.secret_env
        content {
          name = env.key
          value_source {
            secret_key_ref {
              secret  = env.value
              version = "latest"
            }
          }
        }
      }
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  labels = var.labels

  lifecycle {
    ignore_changes = [
      labels, # Avoid issues with labels managed by Google
    ]
  }
}

resource "google_cloud_run_service_iam_member" "allow_unauthenticated" {
  count = var.allow_unauthenticated ? 1 : 0

  location = google_cloud_run_v2_service.default.location
  project  = google_cloud_run_v2_service.default.project
  service  = google_cloud_run_v2_service.default.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}
