project_id = "your-gcp-project-id"
region     = "us-central1"
service_name = "fastapi-cloudrun"
image      = "us-central1-docker.pkg.dev/your-gcp-project-id/fastapi/fastapi:latest"

allow_unauthenticated = true
min_instances         = 0
max_instances         = 5
cpu                   = "1"
memory                = "512Mi"
concurrency           = 80

firebase_location = "us-central"
create_artifact_registry = true
create_scheduler      = false

# Example labels - the 'env' label is added automatically from the ENVIRONMENT var below
app_labels = {
  app = "secretsanta"
}

# Plaintext environment variables
env = {
  ENVIRONMENT = "production"
  LOG_LEVEL   = "INFO"
  BASE_URL    = "https://your-service-url.com" # Replace with your actual domain or leave as is
}

# Secrets to be created in Secret Manager and injected as environment variables
secrets = {
  SECRET_KEY              = "replace-with-strong-secret"
  SENDGRID_API_KEY        = "sg.xxx-replace-me"
  AFFILIATE_TAG_AMAZON_IN = "yourtag-21"
}
