project_id   = "your-project"
region       = "asia-south1"
service_name = "your-project"
image        = "asia-south1-docker.pkg.dev/your-project/your-project/your-project-api:latest"
cloud_run_container_port = 8000

allow_unauthenticated = true
min_instances         = 0
max_instances         = 5
cpu                   = "1"
memory                = "512Mi"

firebase_location        = "asia-south1"
create_scheduler         = false
create_artifact_registry = true

# Example labels - the 'env' label is added automatically from the ENVIRONMENT var below
app_labels = {
  app = "your-project"
}
 
# Plaintext environment variables
env = {
  ENVIRONMENT = "production"
  LOG_LEVEL   = "INFO"
  BASE_URL    = "https://your-project.com/"
  FIREBASE_PROJECT_ID = "your-project"
}

# Secrets to be created in Secret Manager and injected as environment variables
secrets = {
  SECRET_KEY = "6qr42p6R3p1hNh5uQh3Vgpi6hrR031FKMv1wjmzehE1gpi6hrR031FK9R1ngan50"
}

create_workload_identity              = true
github_repository                     = "yourname/your-project"
workload_identity_attribute_condition = "attribute.repository == \"yourname/your-project\" && attribute.sub == \"repo:yourname/your-project:ref:refs/heads/main\""

artifact_registry_location   = "asia-south1"
artifact_registry_repository = "your-project"
