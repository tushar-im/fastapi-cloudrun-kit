locals {
  # List of services required for the core setup.
  core_services = [
    "run.googleapis.com",
    "secretmanager.googleapis.com",
    "cloudbuild.googleapis.com",
    "firestore.googleapis.com",
    "iam.googleapis.com",
  ]

  # Additional services for optional features.
  scheduler_service         = ["cloudscheduler.googleapis.com"]
  artifact_registry_service = ["artifactregistry.googleapis.com"]

  # Combine lists based on optional flags.
  enabled_services = toset(concat(
    local.core_services,
    var.create_scheduler ? local.scheduler_service : [],
    var.create_artifact_registry ? local.artifact_registry_service : [],
  ))

  # Merge user-defined labels with the environment label
  env_label = var.env["ENVIRONMENT"] != null ? { env = var.env["ENVIRONMENT"] } : {}
  labels    = merge(var.app_labels, local.env_label)

  artifact_registry_location   = coalesce(var.artifact_registry_location, var.region)
  artifact_registry_repository = coalesce(var.artifact_registry_repository, "${var.service_name}-repo")
}

module "project_services" {
  source     = "./modules/project-services"
  project_id = var.project_id
  services   = local.enabled_services
}

module "service_account" {
  source     = "./modules/service-account"
  project_id = var.project_id
  name       = "${var.service_name}-runner"

  # Grant extra permissions if optional features are enabled.
  enable_scheduler_token_creator  = var.create_scheduler
  enable_artifact_registry_reader = var.create_artifact_registry
  enable_artifact_registry_writer = var.create_artifact_registry
  enable_artifact_registry_repo_admin = var.grant_artifact_registry_repo_admin

  depends_on = [module.project_services]
}

module "artifact_registry" {
  count = var.create_artifact_registry ? 1 : 0

  source        = "./modules/artifact-registry"
  project_id    = var.project_id
  location      = local.artifact_registry_location
  repository_id = local.artifact_registry_repository
  labels        = local.labels
  description   = "Docker images for ${var.service_name}"

  depends_on = [module.project_services]
}

module "workload_identity" {
  count = var.create_workload_identity ? 1 : 0

  source                = "./modules/workload-identity"
  project_id            = var.project_id
  service_account_email = module.service_account.email
  github_repository     = var.github_repository
  pool_id               = var.workload_identity_pool_id
  pool_display_name     = var.workload_identity_pool_display_name
  provider_id           = var.workload_identity_provider_id
  provider_display_name = var.workload_identity_provider_display_name
  attribute_condition   = var.workload_identity_attribute_condition
  allowed_audiences     = var.workload_identity_allowed_audiences
}

module "secrets" {
  source     = "./modules/secrets"
  project_id = var.project_id
  secrets    = var.secrets
  labels     = local.labels
  depends_on = [module.project_services]
}


module "firestore" {
  source      = "./modules/firestore"
  project_id  = var.project_id
  location_id = var.firebase_location

  depends_on = [module.project_services]
}

module "cloud_run" {
  source                = "./modules/cloud-run"
  project_id            = var.project_id
  region                = var.region
  service_name          = var.service_name
  image                 = var.image
  container_port        = var.cloud_run_container_port
  service_account_email = module.service_account.email
  allow_unauthenticated = var.allow_unauthenticated
  env                   = var.env
  secret_env            = module.secrets.secret_ids
  cpu                   = var.cpu
  memory                = var.memory
  concurrency           = var.concurrency
  min_instances         = var.min_instances
  max_instances         = var.max_instances
  labels                = local.labels

  depends_on = [
    module.project_services,
    module.service_account,
    module.secrets,
    module.firestore,
  ]
}

module "scheduler" {
  count                 = var.create_scheduler ? 1 : 0
  source                = "./modules/scheduler"
  project_id            = var.project_id
  region                = var.region
  name                  = var.scheduler_name
  schedule              = var.scheduler_schedule
  http_target_url       = "${module.cloud_run.url}/health"
  service_account_email = module.service_account.email
  labels                = local.labels

  depends_on = [module.cloud_run]
}
