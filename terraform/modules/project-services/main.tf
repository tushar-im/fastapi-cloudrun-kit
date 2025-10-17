resource "google_project_service" "enabled_service" {
  for_each = toset(var.services)

  project                    = var.project_id
  service                    = each.key
  disable_on_destroy         = true
  disable_dependent_services = true
}
