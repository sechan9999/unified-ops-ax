#!/usr/bin/env bash
# Deploy Unified Ops AX Backend to Google Cloud Run
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-agentichackathon-506620}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="unified-ops-ax"

echo "=== 1. Setting GCP Active Project to ${PROJECT_ID} ==="
gcloud config set project "${PROJECT_ID}"

echo "=== 2. Enabling Required GCP APIs ==="
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com --project "${PROJECT_ID}"

echo "=== 3. Deploying Source Directly to Google Cloud Run (${REGION}) ==="
gcloud run deploy "${SERVICE_NAME}" \
  --source . \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},DEFAULT_LLM_PROVIDER=vertex,CLOUD_RUN_SERVICE_URL=https://unified-ops-ax-652787573242.us-central1.run.app" \
  --project "${PROJECT_ID}"

echo "=== Cloud Run Deployment Successful! ==="
gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --project "${PROJECT_ID}" --format 'value(status.url)'
