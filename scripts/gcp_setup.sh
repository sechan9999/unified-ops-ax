#!/usr/bin/env bash
# Enable required Google Cloud Infrastructure APIs & services
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-agentichackathon-506620}"

echo "=== Enabling GCP APIs for Project: ${PROJECT_ID} ==="
gcloud services enable \
  run.googleapis.com \
  aiplatform.googleapis.com \
  firestore.googleapis.com \
  pubsub.googleapis.com \
  sqladmin.googleapis.com \
  storage.googleapis.com \
  cloudbuild.googleapis.com \
  --project "${PROJECT_ID}"

echo "=== Creating GCP Pub/Sub Activity Topic ==="
gcloud pubsub topics create activity-events --project "${PROJECT_ID}" || true

echo "=== Creating GCP Firestore Database ==="
gcloud firestore databases create --location=us-central1 --project "${PROJECT_ID}" || true

echo "=== GCP Infrastructure Setup Complete ==="
