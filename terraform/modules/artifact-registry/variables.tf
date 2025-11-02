variable "project_id" {
  description = "The Google Cloud project ID."
  type        = string
}

variable "location" {
  description = "Region where the Artifact Registry repository will be created."
  type        = string
}

variable "repository_id" {
  description = "Identifier for the Artifact Registry repository."
  type        = string
}

variable "description" {
  description = "Optional description for the repository."
  type        = string
  default     = "Docker images for Cloud Run"
}

variable "labels" {
  description = "Labels to apply to the repository."
  type        = map(string)
  default     = {}
}
