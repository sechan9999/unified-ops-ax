from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Unified Ops AX"

    # Database
    database_url: str = "sqlite+pysqlite:///./unified_ops.db"

    # AI Gateway
    default_llm_provider: str = "fake"  # fake | anthropic | openai | onprem | vertex
    anthropic_api_key: Optional[str] = None
    anthropic_model: str = "claude-opus-4-8"
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4o"
    onprem_base_url: str = "http://localhost:11434"
    onprem_model: str = "llama3"

    # Google Cloud Infrastructure, Vertex AI & Agent Platform
    gcp_project_id: str = "agentichackathon-506620"
    gcp_region: str = "us-central1"
    cloud_run_service_url: str = "https://unified-ops-ax-506620-uc.a.run.app"
    agent_platform_url: str = "https://console.cloud.google.com/agent-platform/overview?project=agentichackathon-506620"
    vertex_ai_location: str = "us-central1"
    vertex_ai_model: str = "gemini-1.5-flash"
    firestore_collection: str = "activity_logs"
    pubsub_topic: str = "projects/agentichackathon-506620/topics/activity-events"
    gcs_bucket_name: str = "agentichackathon-506620-rag-docs"
    cloud_sql_instance: Optional[str] = "agentichackathon-506620:us-central1:unified-ops-db"

    # Embeddings
    embedding_provider: str = "fake"  # fake | openai | onprem | vertex
    embedding_dim: int = 384
    onprem_embedding_model: str = "nomic-embed-text"  # keyless local embeddings (Ollama)

    # Vector store
    vector_backend: str = "memory"  # memory | pgvector

    # PII field encryption at rest (unset = plaintext/dev). Production: AES-GCM + KMS.
    pii_key: Optional[str] = None

    # Event-bus worker (transactional outbox poller). Off by default so dev/tests
    # don't spawn a thread; enable in deployment.
    event_worker_enabled: bool = False
    event_worker_interval: float = 2.0

    # Notifier (follow-up delivery). fake = in-memory outbox (dev/test).
    notifier_provider: str = "fake"  # fake | console | smtp | twilio
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_from: Optional[str] = None
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None

    # SaaS orchestration (P2)
    accounting_provider: str = "fake"  # fake | douzone | quickbooks
    calendar_provider: str = "fake"  # fake | msgraph | google
    calendar_user_id: Optional[str] = None  # mailbox for msgraph calendar
    currency: str = "KRW"

    # QuickBooks Online (accounting_provider=quickbooks)
    qbo_access_token: Optional[str] = None  # OAuth2 bearer (user obtains via QBO auth-code flow)
    qbo_realm_id: Optional[str] = None
    qbo_base_url: str = "https://quickbooks.api.intuit.com"
    qbo_customer_ref: str = "1"  # default QBO CustomerRef; real deploys map order->customer

    # Microsoft Graph (SharePoint / Teams connector)
    graph_base_url: str = "https://graph.microsoft.com/v1.0"
    graph_login_url: str = "https://login.microsoftonline.com"
    graph_tenant_id: Optional[str] = None
    graph_client_id: Optional[str] = None
    graph_client_secret: Optional[str] = None
    sharepoint_site_id: Optional[str] = None
    teams_group_id: Optional[str] = None


@lru_cache
def get_settings() -> Settings:
    return Settings()
