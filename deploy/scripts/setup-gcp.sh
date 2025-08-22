#!/bin/bash

# Setup script for Google Cloud Platform deployment
# This script sets up the necessary GCP resources for the FastAPI application

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="${PROJECT_ID:-}"
REGION="${REGION:-us-central1}"
SERVICE_NAME="${SERVICE_NAME:-fastapi-cloudrun-kit}"
FIREBASE_PROJECT_ID="${FIREBASE_PROJECT_ID:-$PROJECT_ID}"

# Print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if required tools are installed
check_requirements() {
    print_status "Checking requirements..."
    
    if ! command -v gcloud &> /dev/null; then
        print_error "gcloud CLI is not installed. Please install it from https://cloud.google.com/sdk/docs/install"
        exit 1
    fi
    
    if ! command -v firebase &> /dev/null; then
        print_warning "Firebase CLI is not installed. Installing via npm..."
        npm install -g firebase-tools
    fi
    
    print_success "Requirements check completed"
}

# Get project ID if not provided
get_project_id() {
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [[ -z "$PROJECT_ID" ]]; then
            print_error "PROJECT_ID is not set and no default project found. Please set PROJECT_ID environment variable or run 'gcloud config set project YOUR_PROJECT_ID'"
            exit 1
        fi
    fi
    
    print_status "Using project: $PROJECT_ID"
    print_status "Using region: $REGION"
    print_status "Using service name: $SERVICE_NAME"
}

# Enable required APIs
enable_apis() {
    print_status "Enabling required Google Cloud APIs..."
    
    local apis=(
        "cloudbuild.googleapis.com"
        "run.googleapis.com"
        "containerregistry.googleapis.com"
        "secretmanager.googleapis.com"
        "firebase.googleapis.com"
        "firestore.googleapis.com"
        "identitytoolkit.googleapis.com"
        "cloudresourcemanager.googleapis.com"
        "iam.googleapis.com"
        "serviceusage.googleapis.com"
    )
    
    for api in "${apis[@]}"; do
        print_status "Enabling $api..."
        gcloud services enable "$api" --project="$PROJECT_ID"
    done
    
    print_success "APIs enabled successfully"
}

# Create service accounts
create_service_accounts() {
    print_status "Creating service accounts..."
    
    # Cloud Run service account
    if ! gcloud iam service-accounts describe "cloud-run-service@$PROJECT_ID.iam.gserviceaccount.com" &>/dev/null; then
        print_status "Creating Cloud Run service account..."
        gcloud iam service-accounts create cloud-run-service \
            --display-name="Cloud Run Service Account" \
            --description="Service account for Cloud Run services" \
            --project="$PROJECT_ID"
    else
        print_warning "Cloud Run service account already exists"
    fi
    
    # Firebase Admin service account
    if ! gcloud iam service-accounts describe "firebase-admin@$PROJECT_ID.iam.gserviceaccount.com" &>/dev/null; then
        print_status "Creating Firebase Admin service account..."
        gcloud iam service-accounts create firebase-admin \
            --display-name="Firebase Admin Service Account" \
            --description="Service account for Firebase Admin SDK" \
            --project="$PROJECT_ID"
    else
        print_warning "Firebase Admin service account already exists"
    fi
    
    print_success "Service accounts created"
}

# Assign IAM roles
assign_iam_roles() {
    print_status "Assigning IAM roles..."
    
    # Cloud Run service account roles
    local cloud_run_roles=(
        "roles/cloudsql.client"
        "roles/secretmanager.secretAccessor"
        "roles/firestore.user"
        "roles/firebase.admin"
        "roles/storage.objectAdmin"
    )
    
    for role in "${cloud_run_roles[@]}"; do
        print_status "Assigning role $role to Cloud Run service account..."
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:cloud-run-service@$PROJECT_ID.iam.gserviceaccount.com" \
            --role="$role" \
            --quiet
    done
    
    # Firebase Admin service account roles
    local firebase_roles=(
        "roles/firebase.admin"
        "roles/firestore.owner"
    )
    
    for role in "${firebase_roles[@]}"; do
        print_status "Assigning role $role to Firebase Admin service account..."
        gcloud projects add-iam-policy-binding "$PROJECT_ID" \
            --member="serviceAccount:firebase-admin@$PROJECT_ID.iam.gserviceaccount.com" \
            --role="$role" \
            --quiet
    done
    
    print_success "IAM roles assigned"
}

# Create secrets in Secret Manager
create_secrets() {
    print_status "Creating secrets in Secret Manager..."
    
    # Generate a random secret key if it doesn't exist
    if ! gcloud secrets describe secret-key --project="$PROJECT_ID" &>/dev/null; then
        print_status "Creating SECRET_KEY secret..."
        SECRET_KEY=$(openssl rand -base64 32)
        echo -n "$SECRET_KEY" | gcloud secrets create secret-key \
            --data-file=- \
            --project="$PROJECT_ID"
    else
        print_warning "SECRET_KEY secret already exists"
    fi
    
    # Create Firebase service account key secret (optional)
    if ! gcloud secrets describe firebase-service-account --project="$PROJECT_ID" &>/dev/null; then
        print_status "Creating Firebase service account key secret..."
        # Create and download the key
        gcloud iam service-accounts keys create temp-firebase-key.json \
            --iam-account="firebase-admin@$PROJECT_ID.iam.gserviceaccount.com" \
            --project="$PROJECT_ID"
        
        # Store in Secret Manager
        gcloud secrets create firebase-service-account \
            --data-file=temp-firebase-key.json \
            --project="$PROJECT_ID"
        
        # Clean up temporary file
        rm temp-firebase-key.json
    else
        print_warning "Firebase service account key secret already exists"
    fi
    
    print_success "Secrets created"
}

# Setup Cloud Build trigger (optional)
setup_cloud_build_trigger() {
    print_status "Setting up Cloud Build trigger..."
    
    # Check if repository is connected (this might need manual setup)
    print_warning "Cloud Build trigger setup requires manual repository connection."
    print_warning "Please connect your repository in the Cloud Build console:"
    print_warning "https://console.cloud.google.com/cloud-build/triggers"
    
    cat << EOF > cloudbuild-trigger.yaml
name: fastapi-cloudrun-kit-deploy
description: Deploy FastAPI Cloud Run Kit on push to main
github:
  owner: YOUR_GITHUB_USERNAME
  name: YOUR_REPOSITORY_NAME
  push:
    branch: ^main$
filename: cloudbuild.yaml
substitutions:
  _SERVICE_NAME: $SERVICE_NAME
  _REGION: $REGION
  _ENVIRONMENT: production
EOF
    
    print_status "Cloud Build trigger configuration saved to cloudbuild-trigger.yaml"
    print_status "Apply it with: gcloud builds triggers create github --trigger-config=cloudbuild-trigger.yaml"
}

# Setup Firebase project
setup_firebase() {
    print_status "Setting up Firebase project..."
    
    # Initialize Firebase if not already done
    if [[ ! -f .firebaserc ]]; then
        print_status "Initializing Firebase project..."
        firebase use --add "$FIREBASE_PROJECT_ID"
    fi
    
    # Deploy Firestore rules and indexes
    if [[ -f firebase/firestore.rules ]]; then
        print_status "Deploying Firestore rules..."
        firebase deploy --only firestore:rules --project="$FIREBASE_PROJECT_ID"
    fi
    
    if [[ -f firebase/firestore.indexes.json ]]; then
        print_status "Deploying Firestore indexes..."
        firebase deploy --only firestore:indexes --project="$FIREBASE_PROJECT_ID"
    fi
    
    if [[ -f firebase/storage.rules ]]; then
        print_status "Deploying Storage rules..."
        firebase deploy --only storage --project="$FIREBASE_PROJECT_ID"
    fi
    
    print_success "Firebase setup completed"
}

# Create build artifacts bucket
create_build_bucket() {
    print_status "Creating Cloud Build artifacts bucket..."
    
    if ! gsutil ls -b "gs://$PROJECT_ID-build-artifacts" &>/dev/null; then
        gsutil mb -p "$PROJECT_ID" -c STANDARD -l "$REGION" "gs://$PROJECT_ID-build-artifacts"
    else
        print_warning "Build artifacts bucket already exists"
    fi
    
    print_success "Build artifacts bucket ready"
}

# Main setup function
main() {
    print_status "Starting GCP setup for FastAPI Cloud Run Kit..."
    
    check_requirements
    get_project_id
    enable_apis
    create_service_accounts
    assign_iam_roles
    create_secrets
    create_build_bucket
    setup_firebase
    setup_cloud_build_trigger
    
    print_success "GCP setup completed successfully!"
    print_status ""
    print_status "Next steps:"
    print_status "1. Review and customize the generated configuration files"
    print_status "2. Connect your repository to Cloud Build (if using the trigger)"
    print_status "3. Deploy your application:"
    print_status "   gcloud builds submit --config cloudbuild.yaml ."
    print_status "4. Or use the deployment script:"
    print_status "   ./deploy/scripts/deploy.sh"
    print_status ""
    print_status "Your Cloud Run service will be available at:"
    print_status "https://$SERVICE_NAME-$(echo $REGION | tr -d '-')-$(echo $PROJECT_ID | tr -d '-').a.run.app"
}

# Run main function
main "$@"