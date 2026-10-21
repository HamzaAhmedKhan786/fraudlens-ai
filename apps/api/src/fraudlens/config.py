from functools import lru_cache

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "FraudLens AI"
    environment: str = "development"
    api_prefix: str = "/api/v1"
    cors_origins: str = "http://localhost:3000"
    allowed_hosts: str = "localhost,127.0.0.1,api,testserver"
    database_url: str = "sqlite+aiosqlite:///./fraudlens.db"
    api_key: str = "fraudlens-local-dev-key"
    kafka_enabled: bool = False
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "fraudlens.investigations.v1"
    kafka_consumer_group: str = "fraudlens-evidence-workers-v1"
    llm_provider: str = "disabled"
    openai_api_key: str | None = None
    openai_model: str = "gpt-5-mini"
    groq_api_key: str | None = None
    groq_base_url: str = "https://api.groq.com/openai/v1"
    groq_model: str = "openai/gpt-oss-20b"
    ollama_base_url: str = "http://localhost:11434/v1"
    ollama_model: str = "llama3.2:3b"
    ollama_api_key: str = "ollama"
    max_agent_steps: int = Field(default=12, ge=1, le=100)
    agent_timeout_seconds: int = Field(default=30, ge=1, le=300)
    knowledge_base_path: str = "docs/knowledge-base"
    knowledge_max_chunks: int = Field(default=4, ge=1, le=10)
    knowledge_min_relevance: float = Field(default=0.25, ge=0, le=10)
    minimum_citation_coverage: float = Field(default=1.0, ge=0, le=1)
    max_upload_bytes: int = Field(default=52_428_800, ge=1)
    upload_chunk_bytes: int = Field(default=1_048_576, ge=1)
    object_storage_backend: str = "filesystem"
    object_storage_root: str = ".data/objects"
    object_storage_endpoint: str = "localhost:9000"
    object_storage_access_key: str = "fraudlens"
    object_storage_secret_key: str = "fraudlens-dev-password"
    object_storage_bucket: str = "fraudlens-evidence"
    object_storage_secure: bool = False
    clamav_enabled: bool = False
    clamav_required: bool = False
    clamav_host: str = "localhost"
    clamav_port: int = 3310
    processing_inline: bool = True
    upload_retention_days: int = Field(default=30, ge=1)
    metadata_retention_days: int = Field(default=180, ge=1)
    google_client_id: str | None = None
    google_client_secret: str | None = None
    google_redirect_uri: str = "http://localhost:8000/api/v1/connectors/google/callback"
    google_gmail_scopes: str = "https://www.googleapis.com/auth/gmail.readonly"
    google_token_encryption_key: str | None = None
    oauth_state_ttl_seconds: int = Field(default=600, ge=60, le=3600)
    oidc_enabled: bool = False
    oidc_issuer: str | None = None
    oidc_audience: str | None = None
    oidc_jwks_url: str | None = None
    oidc_tenant_claim: str = "tenant_id"
    oidc_roles_claim: str = "roles"
    microsoft_client_id: str | None = None
    microsoft_client_secret: str | None = None
    microsoft_tenant_id: str = "organizations"
    microsoft_redirect_uri: str = "http://localhost:8000/api/v1/connectors/microsoft/callback"
    stripe_enabled: bool = False
    stripe_secret_key: str | None = None
    stripe_webhook_secret: str | None = None
    stripe_price_individual_monthly: str | None = None
    stripe_price_individual_annual: str | None = None
    stripe_price_small_monthly: str | None = None
    stripe_price_small_annual: str | None = None
    stripe_price_medium_monthly: str | None = None
    stripe_price_medium_annual: str | None = None
    billing_return_url: str = "http://localhost:3000/billing"
    subscription_trial_days: int = Field(default=14, ge=0, le=90)
    ocr_enabled: bool = False
    ocr_languages: str = "eng"
    tesseract_cmd: str = "tesseract"
    tessdata_prefix: str | None = None
    poppler_path: str | None = None
    ocr_max_pages: int = Field(default=20, ge=1, le=200)
    video_inference_enabled: bool = False
    video_inference_url: str | None = None
    video_inference_model: str = "unconfigured"

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        if self.llm_provider not in {"disabled", "openai", "groq", "ollama"}:
            raise ValueError("LLM_PROVIDER must be disabled, openai, groq, or ollama")
        if self.clamav_required and not self.clamav_enabled:
            raise ValueError("CLAMAV_ENABLED must be true when CLAMAV_REQUIRED=true")
        if not self.processing_inline and not self.kafka_enabled:
            raise ValueError("KAFKA_ENABLED must be true when PROCESSING_INLINE=false")
        if self.oidc_enabled and not all(
            (self.oidc_issuer, self.oidc_audience, self.oidc_jwks_url)
        ):
            raise ValueError("OIDC_ISSUER, OIDC_AUDIENCE and OIDC_JWKS_URL are required")
        if self.stripe_enabled and not all((self.stripe_secret_key, self.stripe_webhook_secret)):
            raise ValueError("Stripe keys are required when STRIPE_ENABLED=true")
        if self.stripe_enabled and not self.stripe_secret_key.startswith("sk_test_"):
            raise ValueError("Only Stripe test-mode keys are accepted")
        if self.environment.lower() == "production":
            insecure_keys = {
                "fraudlens-local-dev-key",
                "fraudlens-compose-dev-key",
                "replace-with-a-long-random-secret",
            }
            if self.api_key in insecure_keys or len(self.api_key) < 32:
                raise ValueError("API_KEY must be a unique secret of at least 32 characters")
            if self.database_url.startswith("sqlite"):
                raise ValueError("Production requires PostgreSQL; SQLite is development-only")
            if self.object_storage_backend == "filesystem":
                raise ValueError("Production requires durable object storage such as MinIO or S3")
            if self.google_client_id and not self.google_token_encryption_key:
                raise ValueError("GOOGLE_TOKEN_ENCRYPTION_KEY is required for Gmail in production")
        return self

    @property
    def gmail_scopes(self) -> list[str]:
        return [
            scope.strip()
            for scope in self.google_gmail_scopes.replace(",", " ").split()
            if scope.strip()
        ]

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
