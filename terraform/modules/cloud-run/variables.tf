variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud Run service."
  type        = string
}

variable "service_name" {
  description = "The name of the Cloud Run service."
  type        = string
}

variable "image" {
  description = "The container image to deploy."
  type        = string
}

variable "service_account_email" {
  description = "The email of the service account to run the service with."
  type        = string
}

variable "allow_unauthenticated" {
  description = "Whether to allow unauthenticated access to the service."
  type        = bool
  default     = false
}

variable "env" {
  description = "A map of environment variables."
  type        = map(string)
  default     = {}
}

variable "secret_env" {
  description = "A map of secret names to their full resource IDs for mounting as environment variables."
  type        = map(string)
  default     = {}
  sensitive   = true
}

variable "cpu" {
  description = "The CPU limit for the container."
  type        = string
  default     = "1"
}

variable "memory" {
  description = "The memory limit for the container."
  type        = string
  default     = "512Mi"
}

variable "concurrency" {
  description = "The number of concurrent requests per container."
  type        = number
  default     = 80
}

variable "min_instances" {
  description = "The minimum number of instances."
  type        = number
  default     = 0
}

variable "max_instances" {
  description = "The maximum number of instances."
  type        = number
  default     = 10
}

variable "labels" {
  description = "A map of labels to apply to the service."
  type        = map(string)
  default     = {}
}

variable "timeout_seconds" {
  description = "The request timeout in seconds for the Cloud Run service."
  type        = number
  default     = 300
}

variable "container_port" {
  description = "The port the container listens on."
  type        = number
  default     = 8080
}
