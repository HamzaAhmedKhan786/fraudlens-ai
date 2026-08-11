from functools import lru_cache

from fraudlens.agents.deterministic import (
    DocumentIntegrityAgent,
    EmailSecurityAgent,
    UrlReputationAgent,
)
from fraudlens.agents.llm import DeterministicNarrativeGenerator, OpenAINarrativeGenerator
from fraudlens.agents.risk import RiskEngine
from fraudlens.config import get_settings
from fraudlens.events import InMemoryEventPublisher, KafkaEventPublisher
from fraudlens.orchestrator import InvestigationOrchestrator


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
        narrative = OpenAINarrativeGenerator(settings.openai_api_key, settings.openai_model)
    return InvestigationOrchestrator(
        agents=[EmailSecurityAgent(), DocumentIntegrityAgent(), UrlReputationAgent()],
        risk_engine=RiskEngine(),
        narrative=narrative,
        publisher=get_publisher(),
        max_steps=settings.max_agent_steps,
    )
