# Windows PowerShell script to deploy Unified Ops AX Backend to Google Cloud Run
$ErrorActionPreference = "Continue"

$PROJECT_ID = if ($env:GCP_PROJECT_ID) { $env:GCP_PROJECT_ID } else { "agentichackathon-506620" }
$REGION = if ($env:GCP_REGION) { $env:GCP_REGION } else { "us-central1" }
$SERVICE_NAME = "unified-ops-ax"

Write-Host "=== 1. Setting Active GCP Project to $PROJECT_ID ===" -ForegroundColor Cyan
gcloud config set project $PROJECT_ID

Write-Host "=== 2. Enabling Required GCP APIs (Cloud Run, Cloud Build, Artifact Registry) ===" -ForegroundColor Cyan
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project $PROJECT_ID

Write-Host "=== 3. Deploying Source Directly to Google Cloud Run ($REGION) ===" -ForegroundColor Cyan
gcloud run deploy $SERVICE_NAME `
  --source . `
  --platform managed `
  --region $REGION `
  --allow-unauthenticated `
  --memory 1Gi `
  --cpu 1 `
  --min-instances 0 `
  --max-instances 10 `
  --set-env-vars "GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,DEFAULT_LLM_PROVIDER=vertex" `
  --project $PROJECT_ID

if ($LASTEXITCODE -eq 0) {
    Write-Host "=== 4. Fetching Live Service URL ===" -ForegroundColor Green
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --project $PROJECT_ID --format "value(status.url)"
    Write-Host "========================================================" -ForegroundColor Green
    Write-Host "  Cloud Run Deployment Successful!" -ForegroundColor Green
    Write-Host "  Live Cloud Run URL: $SERVICE_URL" -ForegroundColor Green
    Write-Host "========================================================" -ForegroundColor Green
} else {
    Write-Host "========================================================" -ForegroundColor Red
    Write-Host "  PERMISSION DENIED NOTICE:" -ForegroundColor Red
    Write-Host "  User 'hkchun18@gmail.com' requires IAM roles on project '$PROJECT_ID':" -ForegroundColor Yellow
    Write-Host "  1. Cloud Build Editor (roles/cloudbuild.builds.editor)" -ForegroundColor Yellow
    Write-Host "  2. Storage Admin (roles/storage.admin)" -ForegroundColor Yellow
    Write-Host "  3. Cloud Run Admin (roles/run.admin)" -ForegroundColor Yellow
    Write-Host "  4. Service Account User (roles/iam.serviceAccountUser)" -ForegroundColor Yellow
    Write-Host "========================================================" -ForegroundColor Red
}
