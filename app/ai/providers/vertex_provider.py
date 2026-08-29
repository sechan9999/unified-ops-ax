"""Google Cloud Vertex AI Provider for Gemini Models (Gemini 1.5 Flash / 2.5 Flash / Pro).
Integrates with Google Cloud Vertex AI infrastructure."""
from __future__ import annotations

import os
from typing import Any

from app.ai.providers.base import ChatMessage
from app.config import get_settings


class VertexAIProvider:
    name = "vertex"

    def __init__(self, project: str | None = None, location: str | None = None, model_name: str | None = None) -> None:
        settings = get_settings()
        self.project = project or settings.gcp_project_id
        self.location = location or settings.vertex_ai_location
        self.model_name = model_name or settings.vertex_ai_model

    def complete(self, messages: list[ChatMessage], *, model: str | None = None, **kwargs: Any) -> str:
        target_model = model or self.model_name
        user = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")
        system = next((m["content"] for m in messages if m["role"] == "system"), "")
        grounded = "[grounded] " if "CONTEXT:" in system or "CONTEXT:" in user else ""

        prompt_parts = []
        for m in messages:
            role = m.get("role")
            content = m.get("content", "")
            if role != "system":
                prompt_parts.append(f"{role.upper()}: {content}")

        full_prompt = "\n".join(prompt_parts)

        # Live Vertex AI API call if credentials present
        if os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GCP_PROJECT"):
            try:
                import vertexai
                from vertexai.generative_models import GenerativeModel

                vertexai.init(project=self.project, location=self.location)
                v_model = GenerativeModel(target_model, system_instruction=system or None)
                response = v_model.generate_content(full_prompt)
                return response.text
            except Exception:
                pass

        # Offline / Keyless fallback response
        return f"{grounded}(vertex-ai:{target_model}@{self.location}) answer to: {user[:280]}"
