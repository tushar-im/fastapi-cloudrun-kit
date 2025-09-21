#!/bin/bash

# Simple interactive runner for Terraform commands.

set -e # Exit immediately if a command exits with a non-zero status.

# --- Helper Functions ---
print_usage() {
  echo "Usage: $0 [plan|apply|destroy] [-f <tfvars_file>]"
  echo "  - If no command is provided, runs interactively."
  echo "  - Commands:"
  echo "    plan      : Runs 'terraform plan'."
  echo "    apply     : Runs 'terraform apply'."
  echo "    destroy   : Runs 'terraform destroy'."
  echo "  - Options:"
  echo "    -f <file> : Specify a .tfvars file to use (e.g., my.tfvars)."
}

check_deps() {
  echo "--- Checking for dependencies (gcloud, terraform) ---"
  if ! command -v gcloud &> /dev/null; then
    echo "ERROR: 'gcloud' command not found. Please install the Google Cloud SDK."
    exit 1
  fi
  if ! command -v terraform &> /dev/null; then
    echo "ERROR: 'terraform' command not found. Please install Terraform."
    exit 1
  fi
  echo "Dependencies found."
}

check_adc() {
  echo "--- Checking for Application Default Credentials (ADC) ---"
  if ! gcloud auth application-default print-access-token --quiet &> /dev/null; then
    echo "WARNING: Application Default Credentials are not set or have expired."
    read -p "Run 'gcloud auth application-default login' now? [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
      gcloud auth application-default login
    else
      echo "Please run 'gcloud auth application-default login' manually."
      exit 1
    fi
  fi
  echo "ADC is configured."
}

# --- Script Logic ---

# Ensure the script is run from the repository root
if [ ! -d "terraform" ]; then
  echo "ERROR: This script must be run from the root of the repository."
  exit 1
fi

cd terraform

# Default values
TF_COMMAND=""
TFVARS_FILE="my.tfvars"

# Parse command-line arguments
while getopts ":f:" opt; do
  case ${opt} in
    f )
      TFVARS_FILE=$OPTARG
      ;;
    \? )
      print_usage
      exit 1
      ;;
  esac
done
shift $((OPTIND -1))

if [ -n "$1" ]; then
  TF_COMMAND=$1
  if [[ ! " plan apply destroy " =~ " ${TF_COMMAND} " ]]; then
    echo "Invalid command: $TF_COMMAND"
    print_usage
    exit 1
  fi
fi

# --- Main Execution ---

check_deps
check_adc

# Interactive Mode
if [ -z "$TF_COMMAND" ]; then
  echo "--- Interactive Mode ---"

  if [ ! -f "$TFVARS_FILE" ]; then
    read -p "Enter your GCP Project ID: " project_id
    read -p "Enter your desired GCP Region [us-central1]: " region
    region=${region:-us-central1}

    echo "Copying 'example.tfvars' to '$TFVARS_FILE' and populating with your values..."
    cp example.tfvars "$TFVARS_FILE"
    sed -i "s/your-gcp-project-id/$project_id/g" "$TFVARS_FILE"
    # Note: This simple sed might not work for all image URL formats, but covers the example.
    echo "Please review and complete '$TFVARS_FILE' before applying."
  fi

  echo "--- Initializing Terraform ---"
  terraform init

  echo "--- Planning Terraform ---"
  terraform plan -var-file="$TFVARS_FILE"

  read -p "Do you want to apply these changes? [y/N] " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "--- Applying Terraform ---"
    terraform apply -var-file="$TFVARS_FILE" -auto-approve
    echo "--- Apply complete! ---"
    URL=$(terraform output -raw cloud_run_url)
    echo "Cloud Run Service URL: $URL"
  else
    echo "Apply cancelled."
  fi

# Non-Interactive (Command) Mode
else
  echo "--- Command Mode: $TF_COMMAND ---"
  if [ ! -f "$TFVARS_FILE" ]; then
    echo "ERROR: TFVARS file '$TFVARS_FILE' not found."
    exit 1
  fi

  echo "--- Initializing Terraform (if needed) ---"
  terraform init

  echo "--- Running 'terraform $TF_COMMAND' ---"
  if [ "$TF_COMMAND" = "apply" ] || [ "$TF_COMMAND" = "destroy" ]; then
      terraform "$TF_COMMAND" -var-file="$TFVARS_FILE" -auto-approve
  else
      terraform "$TF_COMMAND" -var-file="$TFVARS_FILE"
  fi

  if [ "$TF_COMMAND" = "apply" ]; then
    echo "--- Apply complete! ---"
    URL=$(terraform output -raw cloud_run_url)
    echo "Cloud Run Service URL: $URL"
  fi
fi

echo "--- Script finished ---"
