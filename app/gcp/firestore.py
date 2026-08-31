"""Google Cloud Firestore Document Store for Unified Ops AX Activity Logs & State Persistence."""
from __future__ import annotations

import os
from typing import Any

from app.config import get_settings


class GoogleCloudFirestoreStore:
    def __init__(self, project_id: str | None = None, collection_name: str | None = None) -> None:
        settings = get_settings()
        self.project_id = project_id or settings.gcp_project_id
        self.collection_name = collection_name or settings.firestore_collection
        self._local_store: dict[str, dict[str, Any]] = {}

    def save_document(self, doc_id: str, data: dict[str, Any]) -> dict[str, Any]:
        # Live GCP Firestore API call if credentials present
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_PROJECT"):
            try:
                from google.cloud import firestore

                db = firestore.Client(project=self.project_id)
                doc_ref = db.collection(self.collection_name).document(doc_id)
                doc_ref.set(data)
                return {"status": "saved", "doc_id": doc_id, "backend": "firestore"}
            except Exception:
                pass

        # Offline / Keyless local store fallback
        self._local_store[doc_id] = data
        return {"status": "saved_local", "doc_id": doc_id, "backend": "memory_fallback"}

    def get_document(self, doc_id: str) -> dict[str, Any] | None:
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_PROJECT"):
            try:
                from google.cloud import firestore

                db = firestore.Client(project=self.project_id)
                doc_ref = db.collection(self.collection_name).document(doc_id)
                snapshot = doc_ref.get()
                if snapshot.exists:
                    return snapshot.to_dict()
            except Exception:
                pass
        return self._local_store.get(doc_id)

    def list_recent_documents(self, limit: int = 20) -> list[dict[str, Any]]:
        """Fetch recent telemetry audit logs from Firestore or local fallback."""
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_PROJECT"):
            try:
                from google.cloud import firestore

                db = firestore.Client(project=self.project_id)
                docs = db.collection(self.collection_name).limit(limit).stream()
                return [d.to_dict() for d in docs]
            except Exception:
                pass
        return list(self._local_store.values())[-limit:]
