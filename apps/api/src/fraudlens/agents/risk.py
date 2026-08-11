from fraudlens.domain.models import Finding, RiskAssessment, Severity


class RiskEngine:
    """Versioned, deterministic fraud scoring; LLM output never enters this calculation."""

    ruleset_version = "2026.08.1"

    def assess(self, findings: list[Finding]) -> RiskAssessment:
        # Confidence scales each rule contribution; the cap prevents uncontrolled additive scores.
        score = min(100, round(sum(item.risk_points * item.confidence for item in findings)))
        severity = (
            Severity.CRITICAL
            if score >= 80
            else Severity.HIGH
            if score >= 60
            else Severity.MEDIUM
            if score >= 30
            else Severity.LOW
        )
        return RiskAssessment(
            score=score,
            severity=severity,
            ruleset_version=self.ruleset_version,
            finding_ids=[item.id for item in findings],
        )
