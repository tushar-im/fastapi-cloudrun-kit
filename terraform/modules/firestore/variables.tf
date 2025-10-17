variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "location_id" {
  description = "The location of the Firestore database. e.g., us-central."
  type        = string
  default     = "us-central"
}

variable "database_name" {
  description = "The name of the Firestore database."
  type        = string
  default     = "(default)"
}

variable "labels" {
  description = "A map of labels to apply to all created resources."
  type        = map(string)
  default     = {}
}
