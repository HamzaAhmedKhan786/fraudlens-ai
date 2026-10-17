from urllib.parse import urlparse

from fraudlens.agents.base import AgentContext, DeterministicAgent
from fraudlens.domain.models import Finding, Severity


class EmailSecurityAgent(DeterministicAgent):
    name = "email-security"
    supported_kinds = frozenset({"email"})

    async def analyze(self, context: AgentContext) -> list[Finding]:
        findings: list[Finding] = []
        for evidence in filter(self.accepts, context.evidence):
            attrs = evidence.attributes
            if attrs.get("reply_to_mismatch") is True:
                findings.append(
                    Finding(
                        agent=self.name,
                        code="EMAIL_REPLY_TO_MISMATCH",
                        title="Reply-To differs from sender",
                        explanation="The response path does not match the visible sender identity.",
                        severity=Severity.HIGH,
                        confidence=0.99,
                        risk_points=28,
                        evidence_ids=[evidence.id],
                    )
                )
            if any(attrs.get(key) is False for key in ("spf_pass", "dkim_pass", "dmarc_pass")):
                findings.append(
                    Finding(
                        agent=self.name,
                        code="EMAIL_AUTH_FAILURE",
                        title="Email authentication failed",
                        explanation="One or more SPF, DKIM, or DMARC controls did not pass.",
                        severity=Severity.HIGH,
                        confidence=0.98,
                        risk_points=24,
                        evidence_ids=[evidence.id],
                    )
                )
        return findings


class DocumentIntegrityAgent(DeterministicAgent):
    name = "document-integrity"
    supported_kinds = frozenset({"document", "invoice"})

    async def analyze(self, context: AgentContext) -> list[Finding]:
        findings: list[Finding] = []
        for evidence in filter(self.accepts, context.evidence):
            attrs = evidence.attributes
            if attrs.get("iban_changed") is True:
                findings.append(
                    Finding(
                        agent=self.name,
                        code="INVOICE_IBAN_CHANGED",
                        title="Unverified bank account change",
                        explanation=(
                            "The payment account differs from the trusted supplier profile."
                        ),
                        severity=Severity.CRITICAL,
                        confidence=0.97,
                        risk_points=38,
                        evidence_ids=[evidence.id],
                    )
                )
            if attrs.get("metadata_modified") is True:
                findings.append(
                    Finding(
                        agent=self.name,
                        code="DOCUMENT_METADATA_ANOMALY",
                        title="Document metadata anomaly",
                        explanation=(
                            "Modification metadata conflicts with the expected document lifecycle."
                        ),
                        severity=Severity.MEDIUM,
                        confidence=0.82,
                        risk_points=14,
                        evidence_ids=[evidence.id],
                    )
                )
            if attrs.get("payment_change_language") is True:
                findings.append(
                    Finding(
                        agent=self.name,
                        code="PAYMENT_ACCOUNT_CHANGE_REQUEST",
                        title="Payment account change requested",
                        explanation=(
                            "The document asks the recipient to use new or changed bank details. "
                            "Validate the request using a trusted supplier contact channel."
                        ),
                        severity=Severity.HIGH,
                        confidence=0.92,
                        risk_points=32,
                        evidence_ids=[evidence.id],
                    )
                )
            if attrs.get("urgent_payment_language") is True:
                findings.append(
                    Finding(
                        agent=self.name,
                        code="URGENT_PAYMENT_LANGUAGE",
                        title="Urgent payment language detected",
                        explanation=(
                            "The document applies urgency or secrecy pressure around a payment."
                        ),
                        severity=Severity.MEDIUM,
                        confidence=0.86,
                        risk_points=18,
                        evidence_ids=[evidence.id],
                    )
                )
        return findings


class UrlReputationAgent(DeterministicAgent):
    name = "url-reputation"
    supported_kinds = frozenset({"url"})

    async def analyze(self, context: AgentContext) -> list[Finding]:
        findings: list[Finding] = []
        for evidence in filter(self.accepts, context.evidence):
            value = str(evidence.attributes.get("url", evidence.source))
            host = (urlparse(value).hostname or "").lower()
            age = evidence.attributes.get("domain_age_days")
            if isinstance(age, int) and age < 30:
                findings.append(
                    Finding(
                        agent=self.name,
                        code="NEW_DOMAIN",
                        title="Recently registered domain",
                        explanation=(
                            f"The linked domain {host or 'unknown'} is less than 30 days old."
                        ),
                        severity=Severity.HIGH,
                        confidence=0.93,
                        risk_points=22,
                        evidence_ids=[evidence.id],
                    )
                )
        return findings
