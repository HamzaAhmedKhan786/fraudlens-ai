from functools import lru_cache

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
    max_agent_steps: int = 12
    minimum_citation_coverage: float = 1.0
    max_upload_bytes: int = 52_428_800
    upload_chunk_bytes: int = 1_048_576
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
    upload_retention_days: int = 30
    metadata_retention_days: int = 180

    @property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def trusted_hosts(self) -> list[str]:
        return [host.strip() for host in self.allowed_hosts.split(",") if host.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
