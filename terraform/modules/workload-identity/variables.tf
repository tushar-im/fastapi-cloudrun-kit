variable "project_id" {
  description = "The Google Cloud project ID."
  type        = string
}

variable "service_account_email" {
  description = "The email of the service account to bind to Workload Identity."
  type        = string
}

variable "github_repository" {
  description = "GitHub repository in the form <owner>/<repo>."
  type        = string
}

variable "pool_id" {
  description = "Identifier for the Workload Identity Pool."
  type        = string
}

variable "pool_display_name" {
  description = "Display name for the Workload Identity Pool."
  type        = string
  default     = "GitHub Actions Pool"
}

variable "pool_description" {
  description = "Optional description for the Workload Identity Pool."
  type        = string
  default     = "Workload Identity Pool for GitHub Actions deployments."
}

variable "provider_id" {
  description = "Identifier for the Workload Identity Pool Provider."
  type        = string
}

variable "provider_display_name" {
  description = "Display name for the Workload Identity Pool Provider."
  type        = string
  default     = "GitHub Actions Provider"
}

variable "provider_description" {
  description = "Optional description for the Workload Identity Pool Provider."
  type        = string
  default     = "OIDC provider for GitHub Actions."
}

variable "allowed_audiences" {
  description = "List of additional allowed audiences for the GitHub OIDC token."
  type        = list(string)
  default     = []
}

variable "attribute_condition" {
  description = "Optional CEL expression to further restrict which GitHub workflows may impersonate this service account."
  type        = string
  default     = null
}

variable "attribute_mapping_overrides" {
  description = "Optional overrides for attribute mapping on the provider."
  type        = map(string)
  default     = {}
}
