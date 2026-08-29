"""Unit tests for Google Cloud Infrastructure & Vertex AI integrations."""
import os
from app.ai.gateway import get_gateway
from app.ai.embeddings import get_embedder
from app.gcp.pubsub import GoogleCloudPubSubPublisher
from app.gcp.firestore import GoogleCloudFirestoreStore
from app.gcp.storage import GoogleCloudStorageBucket
from app.preflight import preflight


def test_vertex_ai_gateway_provider():
    gateway = get_gateway()
    res = gateway.chat([{"role": "user", "content": "Test prompt"}], provider="vertex")
    assert res["provider"] == "vertex"
    assert "vertex-ai" in res["content"] or "Processed request" in res["content"]


def test_vertex_ai_embedder():
    from app.ai.embeddings import VertexAIEmbedder
    embedder = VertexAIEmbedder()
    assert embedder.provider == "vertex"
    vectors = embedder.embed(["test document 1", "test document 2"])
    assert len(vectors) == 2
    assert vectors.shape[1] > 0


def test_gcp_pubsub_publisher():
    publisher = GoogleCloudPubSubPublisher()
    res = publisher.publish_event("order.created", {"order_id": "ORD-12345"})
    assert res["status"] in ("published", "queued_local")
    assert res["event_type"] == "order.created"


def test_gcp_firestore_store():
    store = GoogleCloudFirestoreStore()
    save_res = store.save_document("doc-1", {"name": "GCP Audit Item"})
    assert save_res["status"] in ("saved", "saved_local")
    doc = store.get_document("doc-1")
    assert doc is not None
    assert doc["name"] == "GCP Audit Item"


def test_gcp_storage_bucket():
    bucket = GoogleCloudStorageBucket()
    res = bucket.upload_blob("test_doc.txt", "Sample document content for RAG")
    assert res["status"] in ("uploaded", "uploaded_local")
    assert "gs://agentichackathon-506620-rag-docs/test_doc.txt" in res["gcs_uri"]


def test_preflight_gcp_reporting():
    data = preflight()
    assert data["ready"] is True
    assert data["gcp_backend"]["service"] == "Cloud Run"
    assert "https://unified-ops-ax-652787573242.us-central1.run.app" in data["gcp_backend"]["url"]
    gcp_checks = [c for c in data["checks"] if c["subsystem"].startswith("gcp_")]
    assert len(gcp_checks) >= 2
