variable "project_id" {
  description = "The GCP project ID."
  type        = string
}

variable "region" {
  description = "The GCP region for the repository."
  type        = string
}

variable "repository" {
  description = "The name of the Artifact Registry repository."
  type        = string
  default     = "fastapi"
}

variable "labels" {
  description = "A map of labels to apply to all created resources."
  type        = map(string)
  default     = {}
}
