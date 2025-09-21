variable "project_id" {
  description = "The GCP project ID where the services will be enabled."
  type        = string
}

variable "services" {
  description = "A list of Google Cloud services to enable."
  type        = list(string)
  default     = []
}
