terraform {
  required_version = ">= 1.13"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 7.30.0"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = ">= 7.30.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.0.0"
    }
  }
}
