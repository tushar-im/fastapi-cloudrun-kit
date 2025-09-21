output "id" {
  description = "The full ID of the Cloud Run service."
  value       = google_cloud_run_v2_service.default.id
}

output "url" {
  description = "The URL of the Cloud Run service."
  value       = google_cloud_run_v2_service.default.uri
}

output "service_name" {
  description = "The name of the Cloud Run service."
  value       = google_cloud_run_v2_service.default.name
}
