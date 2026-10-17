import asyncio
from time import perf_counter

from fraudlens.agents.base import AgentContext, DeterministicAgent
from fraudlens.agents.llm import NarrativeGenerator
from fraudlens.agents.risk import RiskEngine
from fraudlens.domain.models import AgentTrace, Finding, InvestigationReport, InvestigationRequest
from fraudlens.events import EventPublisher


class InvestigationOrchestrator:
    def __init__(
        self,
        agents: list[DeterministicAgent],
        risk_engine: RiskEngine,
        narrative: NarrativeGenerator,
        publisher: EventPublisher,
        max_steps: int = 12,
    ) -> None:
        self._agents = agents
        self._risk_engine = risk_engine
        self._narrative = narrative
        self._publisher = publisher
        self._max_steps = max_steps

    async def investigate(
        self, request: InvestigationRequest, critical_threshold: int = 80
    ) -> InvestigationReport:
        applicable = [agent for agent in self._agents if any(map(agent.accepts, request.evidence))]
        if len(applicable) > self._max_steps:
            raise ValueError("Investigation exceeds the configured agent step budget")

        context = AgentContext(request.case_id, request.tenant_id, request.evidence)

        async def run(agent: DeterministicAgent) -> tuple[list[Finding], AgentTrace]:
            started = perf_counter()
            try:
                findings = await agent.analyze(context)
                status = "COMPLETED"
            except Exception:
                findings = []
                status = "FAILED"
            duration = round((perf_counter() - started) * 1000)
            return findings, AgentTrace(
                agent=agent.name, status=status, duration_ms=duration, finding_count=len(findings)
            )

        results = await asyncio.gather(*(run(agent) for agent in applicable))
        findings = [finding for agent_findings, _ in results for finding in agent_findings]
        traces = [trace for _, trace in results]
        risk = self._risk_engine.assess(findings, critical_threshold=critical_threshold)
        summary = await self._narrative.summarize(findings, risk)
        citations = sorted({item for finding in findings for item in finding.evidence_ids})
        report = InvestigationReport(
            case_id=request.case_id,
            tenant_id=request.tenant_id,
            risk=risk,
            findings=findings,
            summary=summary,
            citations=citations,
            agent_trace=traces,
        )
        await self._publisher.publish(
            request.case_id,
            {
                "type": "investigation.completed",
                "version": 1,
                "case_id": request.case_id,
                "investigation_id": str(report.investigation_id),
                "risk_score": risk.score,
                "severity": risk.severity,
            },
        )
        return report
