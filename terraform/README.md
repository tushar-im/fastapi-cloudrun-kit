# Terraform IaC for FastAPI on Cloud Run

This Terraform setup deploys a containerized FastAPI application to Google Cloud Run, with supporting resources like Firestore, Secret Manager, and an optional Artifact Registry and Cloud Scheduler.

## Prerequisites

1.  **Install Tools**:
    *   [Terraform](https://learn.hashicorp.com/tutorials/terraform/install-cli) (version >= 1.13)
    *   [Google Cloud SDK](https://cloud.google.com/sdk/docs/install) (`gcloud`)

2.  **GCP Project**:
    *   Create a new Google Cloud Project or use an existing one.
    *   Ensure **billing is enabled** for your project.

3.  **Authentication**:
    *   Log in to your Google account:
        ```bash
        gcloud auth login
        ```
    *   Set up Application Default Credentials (ADC), which this Terraform configuration uses to authenticate to Google Cloud:
        ```bash
        gcloud auth application-default login
        ```

4.  **Enable APIs**:
    *   The `project-services` module in this configuration will enable all necessary APIs. However, if you run into permissions issues, you may need to enable the `serviceusage.googleapis.com` API manually on your project first.

## Setup & Deployment

This project includes an interactive script to simplify deployment.

### 1. Configure Your Variables

Copy the example variables file:

```bash
cp terraform/example.tfvars terraform/my.tfvars
```

Now, edit `terraform/my.tfvars` and replace the placeholder values:

*   `project_id`: Your GCP project ID.
*   `image`: The full URL of the Docker image you want to deploy. This image must exist in Artifact Registry or another container registry that your project has access to.
*   `secrets`: Update the placeholder values for secrets that will be created in Secret Manager.
*   Review other variables like `region`, `service_name`, etc., and adjust as needed.

### 2. Run the Interactive Script

The easiest way to deploy is to use the `tf.sh` script.

```bash
# Make sure the script is executable
chmod +x terraform/scripts/tf.sh

# Run the script from the repository root
./terraform/scripts/tf.sh
```

The script will:
1.  Check for `gcloud` and `terraform`.
2.  Verify your ADC credentials.
3.  Run `terraform init`.
4.  Run `terraform plan` and show you the proposed changes.
5.  Ask for your confirmation before running `terraform apply`.
6.  Output the final Cloud Run service URL upon completion.

### 3. Manual Terraform Commands

If you prefer to run Terraform commands manually, `cd` into the `terraform` directory and run:

```bash
# Initialize Terraform
terraform init

# Plan the deployment
terraform plan -var-file="my.tfvars"

# Apply the changes
terraform apply -var-file="my.tfvars"
```

## Optional: GCS Remote State

For collaboration or production environments, it is highly recommended to use a remote backend to store the Terraform state file.

1.  **Create a GCS Bucket**: Create a globally unique GCS bucket to store your state file.
    ```bash
    gsutil mb gs://<YOUR_UNIQUE_BUCKET_NAME>/
    ```
    Enable versioning on the bucket to keep a history of your state files:
    ```bash
    gsutil versioning set on gs://<YOUR_UNIQUE_BUCKET_NAME>/
    ```

2.  **Configure the Backend**:
    *   Uncomment the contents of `terraform/backend.tf`.
    *   Replace `<YOUR_STATE_BUCKET>` with the name of the bucket you just created.
    *   Run `terraform init` again. Terraform will ask if you want to copy the existing state to the new GCS backend. Type `yes`.

## Updating the Service

To deploy a new version of your application:

1.  Build and push your new container image to Artifact Registry (or your chosen registry).
2.  Update the `image` variable in your `.tfvars` file to point to the new image tag.
3.  Run the script or `terraform apply` again. Terraform will detect the change and deploy a new revision of the Cloud Run service.
