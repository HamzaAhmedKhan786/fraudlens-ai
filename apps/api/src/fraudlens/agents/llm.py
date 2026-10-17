import json
from typing import Protocol

from fraudlens.domain.models import Finding, RiskAssessment


class NarrativeGenerator(Protocol):
    async def summarize(self, findings: list[Finding], risk: RiskAssessment) -> str: ...


class DeterministicNarrativeGenerator:
    async def summarize(self, findings: list[Finding], risk: RiskAssessment) -> str:
        if not findings:
            return (
                "No configured deterministic fraud indicators were detected. "
                "Human review remains required."
            )
        titles = "; ".join(item.title for item in findings[:5])
        return (
            f"The case has a {risk.severity.lower()} deterministic risk score of {risk.score}/100. "
            f"Primary findings: {titles}. Validate the cited evidence before taking action."
        )


class OpenAICompatibleNarrativeGenerator:
    """Evidence-grounded narrative only; this component cannot change findings or risk."""

    def __init__(self, api_key: str, model: str, base_url: str | None = None) -> None:
        from openai import AsyncOpenAI

        self._client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        self._model = model

    async def summarize(self, findings: list[Finding], risk: RiskAssessment) -> str:
        payload = {
            "risk": risk.model_dump(mode="json"),
            "findings": [item.model_dump(mode="json") for item in findings],
        }
        response = await self._client.responses.create(
            model=self._model,
            instructions=(
                "You are a fraud investigation narrator. Summarize only the supplied findings. "
                "Never add evidence, change the score, or state that fraud is proven. "
                "Reference evidence IDs."
            ),
            input=json.dumps(payload),
        )
        return response.output_text
