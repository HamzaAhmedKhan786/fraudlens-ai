import "server-only";

const baseUrl = process.env.FRAUDLENS_API_URL ?? "http://127.0.0.1:8000/api/v1";
const apiKey = process.env.FRAUDLENS_API_KEY ?? "fraudlens-local-dev-key";

export type CaseSummary = {
  id: string;
  tenant_id: string;
  subject: string;
  case_type: string;
  status: string;
  risk_score: number;
  severity: string;
  evidence_count: number;
  created_at: string;
  updated_at: string;
};

export type DashboardMetrics = {
  open_cases: number;
  critical_cases: number;
  high_risk_cases: number;
  completed_investigations: number;
  average_risk: number;
  agent_confidence: number;
  priority_cases: CaseSummary[];
};

export type InvestigationSummary = { id: string; case_id: string; status: string; risk_score: number; severity: string; created_at: string };
export type AgentStatus = { id: string; name: string; category: string; mode: string; status: string; supported_kinds: string[]; description: string };
export type PolicyDefinition = { id: string; name: string; version: string; enabled: boolean; threshold: number; description: string };
export type ModelHealth = { id: string; name: string; provider: string; status: string; latency_ms: number | null; last_checked: string; detail: string };
export type AuditEntry = { id: string; actor: string; action: string; resource_id: string; payload: Record<string, unknown>; created_at: string };
export type EntityGraph = { nodes: { id: string; label: string; kind: string; risk: number }[]; edges: { source: string; target: string; relation: string }[] };
export type CaseDetail = CaseSummary & { evidence: { id: string; kind: string; source: string; attributes: Record<string, unknown>; sha256?: string | null }[]; latest_report: { summary: string; citations: string[]; risk: { score: number; severity: string }; findings: { id: string; title: string; explanation: string; confidence: number; severity: string; evidence_ids: string[] }[] } | null };

export async function backendFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${baseUrl}${path}`, {
    ...init,
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      "X-API-Key": apiKey,
      "X-Tenant-ID": "demo",
      "X-Actor": "web-console",
      ...init.headers,
    },
  });
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`FraudLens API ${response.status}: ${body}`);
  }
  return response.json() as Promise<T>;
}

export async function getDashboard(): Promise<DashboardMetrics> {
  return backendFetch<DashboardMetrics>("/dashboard");
}
