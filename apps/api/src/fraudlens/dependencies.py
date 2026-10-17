from functools import lru_cache

from fraudlens.agents.deterministic import (
    DocumentIntegrityAgent,
    EmailSecurityAgent,
    UrlReputationAgent,
)
from fraudlens.agents.llm import (
    DeterministicNarrativeGenerator,
    OpenAICompatibleNarrativeGenerator,
)
from fraudlens.agents.risk import RiskEngine
from fraudlens.config import get_settings
from fraudlens.events import InMemoryEventPublisher, KafkaEventPublisher
from fraudlens.gmail import GmailConnector
from fraudlens.ingestion import IngestionService
from fraudlens.orchestrator import InvestigationOrchestrator
from fraudlens.parsers import EvidenceParser
from fraudlens.scanner import VirusScanner
from fraudlens.storage import FilesystemObjectStorage, MinioObjectStorage


@lru_cache
def get_publisher():
    settings = get_settings()
    if settings.kafka_enabled:
        return KafkaEventPublisher(settings.kafka_bootstrap_servers, settings.kafka_topic)
    return InMemoryEventPublisher()


@lru_cache
def get_orchestrator() -> InvestigationOrchestrator:
    settings = get_settings()
    narrative = DeterministicNarrativeGenerator()
    if settings.llm_provider == "openai" and settings.openai_api_key:
        narrative = OpenAICompatibleNarrativeGenerator(
            settings.openai_api_key, settings.openai_model
        )
    elif settings.llm_provider == "groq" and settings.groq_api_key:
        narrative = OpenAICompatibleNarrativeGenerator(
            settings.groq_api_key,
            settings.groq_model,
            base_url=settings.groq_base_url,
        )
    return InvestigationOrchestrator(
        agents=[EmailSecurityAgent(), DocumentIntegrityAgent(), UrlReputationAgent()],
        risk_engine=RiskEngine(),
        narrative=narrative,
        publisher=get_publisher(),
        max_steps=settings.max_agent_steps,
    )


@lru_cache
def get_storage():
    settings = get_settings()
    if settings.object_storage_backend == "minio":
        return MinioObjectStorage(
            endpoint=settings.object_storage_endpoint,
            access_key=settings.object_storage_access_key,
            secret_key=settings.object_storage_secret_key,
            bucket=settings.object_storage_bucket,
            secure=settings.object_storage_secure,
        )
    return FilesystemObjectStorage(settings.object_storage_root, settings.object_storage_bucket)


@lru_cache
def get_scanner() -> VirusScanner:
    settings = get_settings()
    return VirusScanner(
        enabled=settings.clamav_enabled,
        required=settings.clamav_required,
        host=settings.clamav_host,
        port=settings.clamav_port,
    )


@lru_cache
def get_ingestion_service() -> IngestionService:
    return IngestionService(
        settings=get_settings(),
        storage=get_storage(),
        scanner=get_scanner(),
        parser=EvidenceParser(get_settings()),
        publisher=get_publisher(),
        orchestrator=get_orchestrator(),
    )


@lru_cache
def get_gmail_connector() -> GmailConnector:
    return GmailConnector(get_settings(), get_ingestion_service())
