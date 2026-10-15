import pytest
from fraudlens.config import Settings
from pydantic import ValidationError


def test_openai_provider_requires_api_key() -> None:
    with pytest.raises(ValidationError, match="OPENAI_API_KEY"):
        Settings(llm_provider="openai", openai_api_key=None)


def test_required_clamav_must_be_enabled() -> None:
    with pytest.raises(ValidationError, match="CLAMAV_ENABLED"):
        Settings(clamav_required=True, clamav_enabled=False)


def test_async_processing_requires_kafka() -> None:
    with pytest.raises(ValidationError, match="KAFKA_ENABLED"):
        Settings(processing_inline=False, kafka_enabled=False)


def test_production_rejects_development_defaults() -> None:
    with pytest.raises(ValidationError, match="API_KEY"):
        Settings(environment="production")


def test_production_accepts_secure_external_services() -> None:
    settings = Settings(
        environment="production",
        api_key="a-unique-production-service-key-with-32-characters",
        database_url="postgresql+asyncpg://fraudlens:secret@database/fraudlens",
        object_storage_backend="minio",
    )
    assert settings.environment == "production"
