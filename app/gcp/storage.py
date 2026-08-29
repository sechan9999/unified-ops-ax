"""Google Cloud Storage Bucket Connector for RAG Document Assets."""
from __future__ import annotations

import os
from typing import Any

from app.config import get_settings


class GoogleCloudStorageBucket:
    def __init__(self, bucket_name: str | None = None, project_id: str | None = None) -> None:
        settings = get_settings()
        self.bucket_name = bucket_name or settings.gcs_bucket_name
        self.project_id = project_id or settings.gcp_project_id
        self._local_blobs: dict[str, bytes] = {}

    def upload_blob(self, blob_name: str, content: bytes | str, content_type: str = "text/plain") -> dict[str, Any]:
        data = content.encode("utf-8") if isinstance(content, str) else content

        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_PROJECT"):
            try:
                from google.cloud import storage

                client = storage.Client(project=self.project_id)
                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(blob_name)
                blob.upload_from_string(data, content_type=content_type)
                return {
                    "status": "uploaded",
                    "bucket": self.bucket_name,
                    "blob": blob_name,
                    "gcs_uri": f"gs://{self.bucket_name}/{blob_name}",
                }
            except Exception:
                pass

        self._local_blobs[blob_name] = data
        return {
            "status": "uploaded_local",
            "bucket": self.bucket_name,
            "blob": blob_name,
            "gcs_uri": f"gs://{self.bucket_name}/{blob_name}",
        }
