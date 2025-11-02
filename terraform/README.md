# Terraform IaC for FastAPI on Cloud Run

This Terraform setup deploys a containerized FastAPI application to Google Cloud Run, with supporting resources like Firestore, Secret Manager, and an optional Cloud Scheduler.

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
cp terraform/example.tfvars terraform/terraform.tfvars
```

Now, edit `terraform/terraform.tfvars` and replace the placeholder values:

*   `project_id`: Your GCP project ID.
*   `image`: The container image URL Cloud Run should run (for example `asia-south1-docker.pkg.dev/<project>/<repository>/<service>:tag`). If you deploy from source, Terraform still needs a value but it will be replaced on the next GitHub Action run.
*   `secrets`: Update the placeholder values for secrets that will be created in Secret Manager.
*   Set `create_artifact_registry = true`, optionally override `artifact_registry_location`/`artifact_registry_repository`, and point the `image` variable at the tag you plan to push if you want Terraform to provision an Artifact Registry repository for Docker images.
*   Set `create_workload_identity = true` and provide `github_repository = "owner/repo"` (for example, `yourname/your-fastapi-project`) if you want Terraform to configure Workload Identity Federation for GitHub Actions. The apply step will output the Workload Identity Provider resource name you feed into the GitHub secret `GCP_WORKLOAD_IDENTITY_PROVIDER`.
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
terraform plan -var-file="terraform.tfvars"

# Apply the changes
terraform apply -var-file="terraform.tfvars"
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

Deployments are handled by `.github/workflows/deploy-to-cloudrun.yml`, which authenticates via Workload Identity Federation, builds and pushes a container image to Artifact Registry, and calls the `google-github-actions/deploy-cloudrun` action on pushes to `main`. Ensure the required GitHub secrets (`GCP_PROJECT_ID`, `CLOUD_RUN_REGION`, `CLOUD_RUN_SERVICE_NAME`, `CLOUD_RUN_SERVICE_ACCOUNT`, `GCP_WORKLOAD_IDENTITY_PROVIDER`, `ARTIFACT_REGISTRY_REPOSITORY`) are configured, push your changes, and a new revision will roll out automatically. If you need to redeploy manually, you can still use `gcloud run deploy --image` with the tag you published.

## Custom Domains

Classic Cloud Run domain mappings are only available in specific regions. Because this project deploys to `asia-south1`, you **cannot** attach a custom domain through Cloud Run itself. Use one of the following approaches instead:

1. Keep Cloud Run on its generated URL (e.g. `https://<service>-<hash>.a.run.app`) and create DNS records in your provider (Cloudflare etc..) that point to a Cloudflare Worker, reverse proxy, or load balancer which forwards traffic to Cloud Run.
2. If you need Cloud Run–managed certificates, redeploy the service in a supported region (such as `us-central1`) and enable domain mappings there.

For the current setup, manage DNS directly in Cloudflare and proxy requests to the Cloud Run URL—no Terraform changes are required.

### Using a Cloudflare Worker Proxy (asia-south1 example)

Because Cloud Run in `asia-south1` does not support custom domain mappings, you can front the service with a Cloudflare Worker:

1. **Create a Worker** and paste the following code:
   ```js
   export default {
     async fetch(request, env) {
       const backend = new URL(env.BACKEND_URL);
       const incoming = new URL(request.url);
       const target = new URL(incoming.pathname + incoming.search, backend);
       target.protocol = 'https:';

       const init = {
         method: request.method,
         headers: new Headers(request.headers),
         body: request.body,
         redirect: 'manual',
       };

       init.headers.set('Host', backend.host);

       return fetch(target.toString(), init);
     },
   };
   ```

2. **Add a Worker variable** named `BACKEND_URL` with the Cloud Run URL (for example `https://your-project-q3xoi3srwq-el.a.run.app`) and deploy the Worker.

3. **Configure a route** under *Workers → Triggers → Routes* (e.g. `api.your-project.com/*`).

4. **Create a proxied DNS record** in Cloudflare for `api.your-project.com` (CNAME to `your-project.com`, orange-cloud enabled).

Traffic to `https://api.your-project.com` now terminates at Cloudflare, the Worker forwards it to Cloud Run with the correct host header, and the response is proxied back to the client. No changes to Terraform are required for this setup.
