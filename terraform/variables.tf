variable "project_id" {
  description = "The GCP project ID to deploy resources to."
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources in."
  type        = string
  default     = "us-central1"
}

variable "service_name" {
  description = "The name of the Cloud Run service."
  type        = string
  default     = "fastapi-cloudrun"
}

variable "image" {
  description = "The container image to deploy to Cloud Run. e.g., us-central1-docker.pkg.dev/your-gcp-project-id/fastapi/fastapi:latest"
  type        = string
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated access to the Cloud Run service."
  type        = bool
  default     = true
}

variable "min_instances" {
  description = "The minimum number of container instances for the Cloud Run service."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "The maximum number of container instances for the Cloud Run service."
  type        = number
  default     = 5
}

variable "cpu" {
  description = "The CPU limit for the Cloud Run container. e.g., '1' for 1 vCPU."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "The memory limit for the Cloud Run container. e.g., '512Mi'."
  type        = string
  default     = "512Mi"
}

variable "concurrency" {
  description = "The number of concurrent requests a container instance can receive."
  type        = number
  default     = 80
}

variable "firebase_location" {
  description = "The location for the Firestore Native database."
  type        = string
  default     = "us-central"
}

variable "create_artifact_registry" {
  description = "Whether to create an Artifact Registry repository."
  type        = bool
  default     = true
}

variable "create_scheduler" {
  description = "Whether to create a Cloud Scheduler job."
  type        = bool
  default     = false
}

variable "env" {
  description = "A map of environment variables to set in the Cloud Run service."
  type        = map(string)
  default     = {}
}

variable "secrets" {
  description = "A map of secrets to create in Secret Manager. The keys will be the secret names and the values will be the initial secret plaintext."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "scheduler_name" {
  description = "The name for the Cloud Scheduler job."
  type        = string
  default     = "cloud-run-health-check"
}

variable "scheduler_schedule" {
  description = "The cron schedule for the Cloud Scheduler job."
  type        = string
  default     = "0 6 * * *"
}

variable "app_labels" {
  description = "A map of labels to apply to all resources."
  type        = map(string)
  default = {
    app = "secretsanta"
  }
}
