output "email" {
  description = "The email of the created service account."
  value       = google_service_account.service_account.email
}

output "id" {
  description = "The unique ID of the created service account."
  value       = google_service_account.service_account.id
}

output "member" {
  description = "The IAM member identifier for the service account."
  value       = "serviceAccount:${google_service_account.service_account.email}"
}
