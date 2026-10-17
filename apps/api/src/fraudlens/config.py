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
    max_agent_steps: int = Field(default=12, ge=1, le=100)
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

    @model_validator(mode="after")
    def validate_runtime_configuration(self) -> "Settings":
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY is required when LLM_PROVIDER=openai")
        if self.llm_provider == "groq" and not self.groq_api_key:
            raise ValueError("GROQ_API_KEY is required when LLM_PROVIDER=groq")
        if self.llm_provider not in {"disabled", "openai", "groq"}:
            raise ValueError("LLM_PROVIDER must be disabled, openai, or groq")
        if self.clamav_required and not self.clamav_enabled:
            raise ValueError("CLAMAV_ENABLED must be true when CLAMAV_REQUIRED=true")
        if not self.processing_inline and not self.kafka_enabled:
            raise ValueError("KAFKA_ENABLED must be true when PROCESSING_INLINE=false")
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
        return self

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
