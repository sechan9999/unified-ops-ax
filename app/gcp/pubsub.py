"""Google Cloud Pub/Sub Event Bus Publisher for Unified Ops AX Activity Stream.
Publishes transactional outbox events to GCP Pub/Sub topics for serverless event-driven architecture."""
from __future__ import annotations

import json
import os
from typing import Any

from app.config import get_settings


class GoogleCloudPubSubPublisher:
    def __init__(self, project_id: str | None = None, topic_id: str | None = None) -> None:
        settings = get_settings()
        self.project_id = project_id or settings.gcp_project_id
        self.topic_id = topic_id or settings.pubsub_topic
        self.outbox_buffer: list[dict[str, Any]] = []

    def publish_event(self, event_type: str, payload: dict[str, Any], attributes: dict[str, str] | None = None) -> dict[str, Any]:
        data = {
            "event_type": event_type,
            "payload": payload,
            "project_id": self.project_id,
            "source": "unified-ops-ax",
        }
        attr = attributes or {}
        attr["event_type"] = event_type

        # Live GCP Pub/Sub API publish if credentials present
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_PROJECT"):
            try:
                from google.cloud import pubsub_v1

                publisher = pubsub_v1.PublisherClient()
                topic_path = publisher.topic_path(self.project_id, self.topic_id.split("/")[-1])
                data_str = json.dumps(data, default=str).encode("utf-8")
                future = publisher.publish(topic_path, data=data_str, **attr)
                message_id = future.result(timeout=10.0)
                return {
                    "status": "published",
                    "message_id": message_id,
                    "topic": self.topic_id,
                    "event_type": event_type,
                }
            except Exception as exc:
                pass

        # Keyless / local fallback recording
        record = {
            "status": "queued_local",
            "message_id": f"pubsub-sim-{len(self.outbox_buffer)+1:04d}",
            "topic": self.topic_id,
            "event_type": event_type,
            "payload": payload,
        }
        self.outbox_buffer.append(record)
        return record
