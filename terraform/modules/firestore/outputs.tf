output "database_id" {
  description = "The full resource ID of the Firestore database."
  value       = google_firestore_database.database.id
}

output "name" {
  description = "The name of the Firestore database."
  value       = google_firestore_database.database.name
}
