#!/bin/bash

# Deployment script for FastAPI Cloud Run Kit
# This script builds and deploys the application to Google Cloud Run

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
ENVIRONMENT="${ENVIRONMENT:-production}"
TAG="${TAG:-latest}"
MEMORY="${MEMORY:-1Gi}"
CPU="${CPU:-1}"
MIN_INSTANCES="${MIN_INSTANCES:-1}"
MAX_INSTANCES="${MAX_INSTANCES:-10}"
CONCURRENCY="${CONCURRENCY:-100}"

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

# Show usage information
usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Deploy FastAPI Cloud Run Kit to Google Cloud Run

OPTIONS:
    -p, --project PROJECT_ID    Google Cloud Project ID
    -r, --region REGION         Deployment region (default: us-central1)
    -s, --service SERVICE_NAME  Cloud Run service name (default: fastapi-cloudrun-kit)
    -e, --environment ENV       Environment (default: production)
    -t, --tag TAG              Docker image tag (default: latest)
    --memory MEMORY            Memory allocation (default: 1Gi)
    --cpu CPU                  CPU allocation (default: 1)
    --min-instances MIN        Minimum instances (default: 1)
    --max-instances MAX        Maximum instances (default: 10)
    --concurrency CONCURRENCY  Container concurrency (default: 100)
    --build-only              Only build the image, don't deploy
    --deploy-only             Only deploy (skip build)
    --no-traffic              Deploy without routing traffic
    -h, --help                Show this help message

EXAMPLES:
    $0 -p my-project -r us-west1
    $0 --build-only
    $0 --deploy-only --no-traffic

ENVIRONMENT VARIABLES:
    PROJECT_ID                 Google Cloud Project ID
    REGION                     Deployment region
    SERVICE_NAME               Cloud Run service name
    ENVIRONMENT                Environment name
    GOOGLE_APPLICATION_CREDENTIALS  Path to service account key file
EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -p|--project)
                PROJECT_ID="$2"
                shift 2
                ;;
            -r|--region)
                REGION="$2"
                shift 2
                ;;
            -s|--service)
                SERVICE_NAME="$2"
                shift 2
                ;;
            -e|--environment)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -t|--tag)
                TAG="$2"
                shift 2
                ;;
            --memory)
                MEMORY="$2"
                shift 2
                ;;
            --cpu)
                CPU="$2"
                shift 2
                ;;
            --min-instances)
                MIN_INSTANCES="$2"
                shift 2
                ;;
            --max-instances)
                MAX_INSTANCES="$2"
                shift 2
                ;;
            --concurrency)
                CONCURRENCY="$2"
                shift 2
                ;;
            --build-only)
                BUILD_ONLY=true
                shift
                ;;
            --deploy-only)
                DEPLOY_ONLY=true
                shift
                ;;
            --no-traffic)
                NO_TRAFFIC=true
                shift
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                print_error "Unknown option: $1"
                usage
                exit 1
                ;;
        esac
    done
}

# Validate configuration
validate_config() {
    print_status "Validating configuration..."
    
    if [[ -z "$PROJECT_ID" ]]; then
        PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
        if [[ -z "$PROJECT_ID" ]]; then
            print_error "PROJECT_ID is not set. Use --project or set PROJECT_ID environment variable"
            exit 1
        fi
    fi
    
    # Check if gcloud is authenticated
    if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
        print_error "No active gcloud authentication found. Please run 'gcloud auth login'"
        exit 1
    fi
    
    # Check if required files exist
    if [[ ! -f "Dockerfile" ]]; then
        print_error "Dockerfile not found in current directory"
        exit 1
    fi
    
    if [[ ! -f "pyproject.toml" ]]; then
        print_error "pyproject.toml not found in current directory"
        exit 1
    fi
    
    print_success "Configuration validated"
    print_status "Project: $PROJECT_ID"
    print_status "Region: $REGION"
    print_status "Service: $SERVICE_NAME"
    print_status "Environment: $ENVIRONMENT"
    print_status "Image: gcr.io/$PROJECT_ID/$SERVICE_NAME:$TAG"
}

# Build Docker image
build_image() {
    if [[ "$DEPLOY_ONLY" == true ]]; then
        print_status "Skipping build (deploy-only mode)"
        return
    fi
    
    print_status "Building Docker image..."
    
    # Get git commit SHA for tagging
    local commit_sha=$(git rev-parse HEAD 2>/dev/null || echo "unknown")
    local short_sha=$(echo "$commit_sha" | cut -c1-8)
    
    # Build image with multiple tags
    docker build \
        --target production \
        --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME:$TAG" \
        --tag "gcr.io/$PROJECT_ID/$SERVICE_NAME:$short_sha" \
        --build-arg BUILDKIT_INLINE_CACHE=1 \
        --cache-from "gcr.io/$PROJECT_ID/$SERVICE_NAME:latest" \
        .
    
    print_success "Docker image built successfully"
    
    # Push to Container Registry
    print_status "Pushing image to Container Registry..."
    docker push "gcr.io/$PROJECT_ID/$SERVICE_NAME:$TAG"
    docker push "gcr.io/$PROJECT_ID/$SERVICE_NAME:$short_sha"
    
    print_success "Image pushed successfully"
}

# Deploy to Cloud Run
deploy_service() {
    if [[ "$BUILD_ONLY" == true ]]; then
        print_status "Skipping deployment (build-only mode)"
        return
    fi
    
    print_status "Deploying to Cloud Run..."
    
    local deploy_args=(
        "run" "deploy" "$SERVICE_NAME"
        "--image" "gcr.io/$PROJECT_ID/$SERVICE_NAME:$TAG"
        "--region" "$REGION"
        "--platform" "managed"
        "--memory" "$MEMORY"
        "--cpu" "$CPU"
        "--concurrency" "$CONCURRENCY"
        "--max-instances" "$MAX_INSTANCES"
        "--min-instances" "$MIN_INSTANCES"
        "--timeout" "300"
        "--port" "8000"
        "--execution-environment" "gen2"
        "--cpu-boost"
        "--service-account" "cloud-run-service@$PROJECT_ID.iam.gserviceaccount.com"
    )
    
    # Environment variables
    deploy_args+=(
        "--set-env-vars"
        "ENVIRONMENT=$ENVIRONMENT,FIREBASE_PROJECT_ID=$PROJECT_ID,GOOGLE_CLOUD_PROJECT=$PROJECT_ID"
    )
    
    # Secrets
    deploy_args+=(
        "--set-secrets"
        "SECRET_KEY=secret-key:latest"
    )
    
    # Traffic routing
    if [[ "$NO_TRAFFIC" == true ]]; then
        deploy_args+=("--no-traffic")
        print_status "Deploying without traffic routing"
    else
        deploy_args+=("--allow-unauthenticated")
    fi
    
    # Deploy
    gcloud "${deploy_args[@]}" --project="$PROJECT_ID"
    
    print_success "Deployment completed"
}

# Run health check
health_check() {
    if [[ "$BUILD_ONLY" == true ]] || [[ "$NO_TRAFFIC" == true ]]; then
        return
    fi
    
    print_status "Running health check..."
    
    # Get service URL
    local service_url=$(gcloud run services describe "$SERVICE_NAME" \
        --region="$REGION" \
        --project="$PROJECT_ID" \
        --format="value(status.url)")
    
    if [[ -z "$service_url" ]]; then
        print_warning "Could not determine service URL"
        return
    fi
    
    print_status "Service URL: $service_url"
    
    # Wait for service to be ready
    local max_attempts=30
    local attempt=1
    
    while [[ $attempt -le $max_attempts ]]; do
        print_status "Health check attempt $attempt/$max_attempts..."
        
        if curl -f -s "$service_url/health" > /dev/null; then
            print_success "Health check passed!"
            print_status "Service is running at: $service_url"
            return
        fi
        
        sleep 10
        ((attempt++))
    done
    
    print_error "Health check failed after $max_attempts attempts"
    exit 1
}

# Show deployment summary
show_summary() {
    print_status ""
    print_success "Deployment Summary"
    print_status "=================="
    print_status "Project: $PROJECT_ID"
    print_status "Region: $REGION"
    print_status "Service: $SERVICE_NAME"
    print_status "Environment: $ENVIRONMENT"
    print_status "Image: gcr.io/$PROJECT_ID/$SERVICE_NAME:$TAG"
    print_status ""
    
    if [[ "$BUILD_ONLY" != true ]] && [[ "$NO_TRAFFIC" != true ]]; then
        local service_url=$(gcloud run services describe "$SERVICE_NAME" \
            --region="$REGION" \
            --project="$PROJECT_ID" \
            --format="value(status.url)" 2>/dev/null || echo "")
        
        if [[ -n "$service_url" ]]; then
            print_status "Service URL: $service_url"
            print_status "API Documentation: $service_url/docs"
            print_status "Health Check: $service_url/health"
        fi
    fi
    
    print_status ""
    print_status "Useful commands:"
    print_status "  View logs: gcloud logs tail /projects/$PROJECT_ID/logs/run.googleapis.com%2Fstdout --limit=50"
    print_status "  Update traffic: gcloud run services update-traffic $SERVICE_NAME --to-latest --region=$REGION"
    print_status "  Delete service: gcloud run services delete $SERVICE_NAME --region=$REGION"
}

# Cleanup on exit
cleanup() {
    if [[ $? -ne 0 ]]; then
        print_error "Deployment failed!"
    fi
}

trap cleanup EXIT

# Main deployment function
main() {
    print_status "Starting deployment of FastAPI Cloud Run Kit..."
    
    parse_args "$@"
    validate_config
    build_image
    deploy_service
    health_check
    show_summary
    
    print_success "Deployment completed successfully!"
}

# Run main function
main "$@"