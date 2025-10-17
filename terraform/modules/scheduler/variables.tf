variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for the scheduler job."
  type        = string
}

variable "name" {
  description = "The name of the Cloud Scheduler job."
  type        = string
}

variable "schedule" {
  description = "The cron schedule for the job (e.g., '0 6 * * *')."
  type        = string
}

variable "http_target_url" {
  description = "The URL to be triggered by the scheduler."
  type        = string
}

variable "service_account_email" {
  description = "The email of the service account to use for OIDC authentication."
  type        = string
}

variable "labels" {
  description = "A map of labels to apply to the scheduler job."
  type        = map(string)
  default     = {}
}
