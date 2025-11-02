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

variable "cloud_run_container_port" {
  description = "The port number of containern running on Cloud Run."
  type        = number
  default     = 8000
}

variable "firebase_location" {
  description = "The location for the Firestore Native database."
  type        = string
  default     = "us-central"
}


variable "create_scheduler" {
  description = "Whether to create a Cloud Scheduler job."
  type        = bool
  default     = false
}

variable "create_artifact_registry" {
  description = "Whether to create an Artifact Registry Docker repository for container images."
  type        = bool
  default     = false
}

variable "artifact_registry_location" {
  description = "Region for the Artifact Registry repository. Defaults to the Cloud Run region when null."
  type        = string
  default     = null
}

variable "artifact_registry_repository" {
  description = "Name of the Artifact Registry repository to create. Defaults to the service name when null."
  type        = string
  default     = null
}

variable "grant_artifact_registry_repo_admin" {
  description = "Whether to grant the service account Artifact Registry repo admin permissions (required for retagging images)."
  type        = bool
  default     = true
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
    app = "your-project"
  }
}

variable "create_workload_identity" {
  description = "Whether to configure Workload Identity Federation for GitHub Actions."
  type        = bool
  default     = false
}

variable "github_repository" {
  description = "GitHub repository in the form <owner>/<repo> that will be granted Workload Identity access. Required when create_workload_identity is true."
  type        = string
  default     = null
  validation {
    condition     = !(var.create_workload_identity && var.github_repository == null)
    error_message = "github_repository must be set when create_workload_identity is true."
  }
}

variable "workload_identity_pool_id" {
  description = "Identifier for the Workload Identity Pool."
  type        = string
  default     = "github-actions-pool"
}

variable "workload_identity_pool_display_name" {
  description = "Display name for the Workload Identity Pool."
  type        = string
  default     = "GitHub Actions Pool"
}

variable "workload_identity_provider_id" {
  description = "Identifier for the Workload Identity Pool Provider."
  type        = string
  default     = "github-actions"
}

variable "workload_identity_provider_display_name" {
  description = "Display name for the Workload Identity Pool Provider."
  type        = string
  default     = "GitHub Actions Provider"
}

variable "workload_identity_attribute_condition" {
  description = "Optional attribute condition (CEL expression) restricting which GitHub workflows can impersonate the service account."
  type        = string
  default     = null
}

variable "workload_identity_allowed_audiences" {
  description = "Additional allowed audiences for the GitHub OIDC token."
  type        = list(string)
  default     = []
}
