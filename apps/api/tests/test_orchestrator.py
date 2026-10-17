import pytest
from fraudlens.agents.deterministic import (
    DocumentIntegrityAgent,
    EmailSecurityAgent,
    UrlReputationAgent,
)
from fraudlens.agents.llm import DeterministicNarrativeGenerator
from fraudlens.agents.risk import RiskEngine
from fraudlens.domain.models import Evidence, InvestigationRequest, Severity
from fraudlens.events import InMemoryEventPublisher
from fraudlens.orchestrator import InvestigationOrchestrator


@pytest.mark.asyncio
async def test_orchestrator_produces_cited_deterministic_report() -> None:
    publisher = InMemoryEventPublisher()
    orchestrator = InvestigationOrchestrator(
        [EmailSecurityAgent(), DocumentIntegrityAgent(), UrlReputationAgent()],
        RiskEngine(),
        DeterministicNarrativeGenerator(),
        publisher,
    )
    request = InvestigationRequest(
        case_id="CASE-1001",
        evidence=[
            Evidence(
                id="email-1",
                kind="email",
                source="message.eml",
                attributes={
                    "reply_to_mismatch": True,
                    "spf_pass": False,
                    "dkim_pass": True,
                    "dmarc_pass": False,
                },
            ),
            Evidence(
                id="invoice-1",
                kind="invoice",
                source="invoice.pdf",
                attributes={"iban_changed": True},
            ),
        ],
    )

    report = await orchestrator.investigate(request)

    assert report.risk.score == 88
    assert report.risk.severity is Severity.CRITICAL
    assert set(report.citations) == {"email-1", "invoice-1"}
    assert all(finding.deterministic for finding in report.findings)
    assert publisher.events[0]["type"] == "investigation.completed"


def test_risk_engine_caps_score() -> None:
    from fraudlens.domain.models import Finding

    findings = [
        Finding(
            agent="test",
            code=f"RULE_{i}",
            title="Risk",
            explanation="Test",
            severity=Severity.CRITICAL,
            confidence=1,
            risk_points=100,
            evidence_ids=["e-1"],
        )
        for i in range(3)
    ]
    assert RiskEngine().assess(findings).score == 100


def test_tenant_critical_threshold_changes_classification_not_score() -> None:
    from fraudlens.domain.models import Finding

    findings = [
        Finding(
            agent="test",
            code="THRESHOLD_RULE",
            title="Risk",
            explanation="Test",
            severity=Severity.HIGH,
            confidence=1,
            risk_points=75,
            evidence_ids=["e-1"],
        )
    ]
    default = RiskEngine().assess(findings)
    tenant_policy = RiskEngine().assess(findings, critical_threshold=70)
    assert default.score == tenant_policy.score == 75
    assert default.severity is Severity.HIGH
    assert tenant_policy.severity is Severity.CRITICAL


@pytest.mark.asyncio
async def test_document_agent_scores_extracted_payment_pressure() -> None:
    from fraudlens.agents.base import AgentContext

    agent = DocumentIntegrityAgent()
    findings = await agent.analyze(
        AgentContext(
            case_id="CASE-2002",
            tenant_id="demo",
            evidence=[
                Evidence(
                    id="document-1",
                    kind="document",
                    source="invoice.txt",
                    attributes={
                        "payment_change_language": True,
                        "urgent_payment_language": True,
                    },
                )
            ],
        )
    )

    assert {finding.code for finding in findings} == {
        "PAYMENT_ACCOUNT_CHANGE_REQUEST",
        "URGENT_PAYMENT_LANGUAGE",
    }
    assessment = RiskEngine().assess(findings)
    assert assessment.score == 45
    assert assessment.severity is Severity.MEDIUM
