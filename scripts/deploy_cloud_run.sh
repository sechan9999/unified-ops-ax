#!/usr/bin/env bash
# Deploy Unified Ops AX Backend to Google Cloud Run
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-agentichackathon-506620}"
REGION="${GCP_REGION:-us-central1}"
SERVICE_NAME="unified-ops-ax"
IMAGE="gcr.io/${PROJECT_ID}/${SERVICE_NAME}:latest"

echo "=== Building container image with Google Cloud Build ==="
gcloud builds submit --tag "${IMAGE}" --project "${PROJECT_ID}"

echo "=== Deploying container to Google Cloud Run (${REGION}) ==="
gcloud run deploy "${SERVICE_NAME}" \
  --image "${IMAGE}" \
  --platform managed \
  --region "${REGION}" \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 0 \
  --max-instances 10 \
  --set-env-vars "GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},DEFAULT_LLM_PROVIDER=vertex" \
  --project "${PROJECT_ID}"

echo "=== Cloud Run Deployment Successful! ==="
gcloud run services describe "${SERVICE_NAME}" --platform managed --region "${REGION}" --project "${PROJECT_ID}" --format 'value(status.url)'
