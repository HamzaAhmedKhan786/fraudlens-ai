from abc import ABC, abstractmethod
from dataclasses import dataclass

from fraudlens.domain.models import Evidence, Finding


@dataclass(frozen=True)
class AgentContext:
    case_id: str
    tenant_id: str
    evidence: list[Evidence]


class DeterministicAgent(ABC):
    name: str
    supported_kinds: frozenset[str]

    def accepts(self, evidence: Evidence) -> bool:
        return evidence.kind in self.supported_kinds

    @abstractmethod
    async def analyze(self, context: AgentContext) -> list[Finding]: ...
