variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "name" {
  description = "The name of the service account."
  type        = string
  default     = "fastapi-runner"
}

variable "enable_scheduler_token_creator" {
  description = "If true, grants the Service Account Token Creator role for Cloud Scheduler."
  type        = bool
  default     = false
}
variable "enable_artifact_registry_reader" {
  description = "If true, grants the Artifact Registry Reader role to the service account."
  type        = bool
  default     = false
}

variable "enable_artifact_registry_writer" {
  description = "If true, grants the Artifact Registry Writer role to the service account."
  type        = bool
  default     = false
}

variable "enable_artifact_registry_repo_admin" {
  description = "If true, grants the Artifact Registry Repository Admin role to the service account."
  type        = bool
  default     = false
}
