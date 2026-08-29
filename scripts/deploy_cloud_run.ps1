# Windows PowerShell script to build & deploy Unified Ops AX Backend to Google Cloud Run
$ErrorActionPreference = "Stop"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "agentichackathon-506620" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_NAME = "unified-ops-ax"
$IMAGE = "gcr.io/$PROJECT_ID/${SERVICE_NAME}:latest"

Write-Host "=== 1. Setting GCP Active Project to $PROJECT_ID ===" -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

Write-Host "=== 2. Enabling Required GCP APIs (Cloud Run, Cloud Build, Artifact Registry) ===" -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

Write-Host "=== 3. Building Container Image with Google Cloud Build ===" -ForegroundColor Cyan
gcloud builds submit --tag $IMAGE --project $PROJECT_ID

Write-Host "=== 4. Deploying Service to Google Cloud Run ($REGION) ===" -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME `
  --image $IMAGE `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 10 `
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,DEFAULT_LLM_PROVIDER=vertex" `
  --project $PROJECT_ID

Write-Host "=== 5. Fetching Live Service URL ===" -ForegroundColor Green
$SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format "value(status.url)"
Write-Host "Live Cloud Run URL: $SERVICE_URL" -ForegroundColor Green
