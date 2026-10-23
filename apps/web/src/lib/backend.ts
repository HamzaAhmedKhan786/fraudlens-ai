import "server-only";
import { cookies } from "next/headers";

export const backendBaseUrl = process.env.FRAUDLENS_API_URL ?? "http://127.0.0.1:8000/api/v1";
const apiKey = process.env.FRAUDLENS_API_KEY ?? "fraudlens-local-dev-key";

export async function backendAuthHeaders(): Promise<Record<string, string>> {
  const token=(await cookies()).get("fraudlens_session")?.value;
  const workspace=(await cookies()).get("fraudlens_workspace")?.value;
  if(token)return {Authorization:`Bearer ${token}`,...(workspace?{"X-Workspace-ID":workspace}:{})};
  return { "X-API-Key": apiKey, "X-Tenant-ID": "demo", "X-Actor": "web-console", "X-Roles": "analyst,reviewer,admin" };
}

export type CaseSummary = {
  id: string;
  tenant_id: string;
  subject: string;
  case_type: string;
  analysis_modules: string[];
  evidence_sources: string[];
  status: string;
  risk_score: number;
  severity: string;
  assignee: string | null;
  disposition: string | null;
  evidence_count: number;
  created_at: string;
  updated_at: string;
};

export type DashboardMetrics = {
  data_source: string;
  open_cases: number;
  critical_cases: number;
  high_risk_cases: number;
  completed_investigations: number;
  average_risk: number;
  agent_confidence: number;
  priority_cases: CaseSummary[];
  detection_signals: { name: string; count: number; share: number }[];
};

export type InvestigationSummary = { id: string; case_id: string; status: string; risk_score: number; severity: string; created_at: string };
export type AgentStatus = { id: string; name: string; category: string; mode: string; status: string; supported_kinds: string[]; description: string };
export type PolicyDefinition = { id: string; name: string; version: string; enabled: boolean; threshold: number; description: string };
export type ModelHealth = { id: string; name: string; provider: string; status: string; latency_ms: number | null; last_checked: string; detail: string };
export type AuditEntry = { id: string; actor: string; action: string; resource_id: string; payload: Record<string, unknown>; created_at: string };
export type EntityGraph = { nodes: { id: string; label: string; kind: string; risk: number }[]; edges: { source: string; target: string; relation: string }[] };
export type CaseDetail = CaseSummary & { evidence: { id: string; kind: string; source: string; attributes: Record<string, unknown>; sha256?: string | null }[]; comments: { id: string; author: string; body: string; created_at: string }[]; latest_report: { summary: string; citations: string[]; risk: { score: number; severity: string }; agent_trace: { agent: string; status: string; duration_ms: number; finding_count: number }[]; findings: { id: string; title: string; explanation: string; confidence: number; severity: string; evidence_ids: string[] }[] } | null };
export type WorkspaceSettings = { mandatory_human_review: boolean; llm_narrative_enabled: boolean; critical_risk_threshold: number; evidence_retention_days: number; updated_at: string | null };
export type UploadSummary = { id: string; case_id: string; filename: string; declared_content_type: string | null; detected_content_type: string; size_bytes: number; sha256: string; status: string; scan_status: string; processing_attempts: number; extracted: Record<string, unknown>; error: string | null; object_available: boolean; retention_expires_at: string; metadata_expires_at: string; created_at: string; updated_at: string };
export type UploadList = { items: UploadSummary[]; total: number };
export type PublicIntelligence = { id: string; indicator_type: string; indicator: string; provider: string; source_uri: string; status: string; facts: Record<string, unknown>; fetched_at: string };
export type GmailConnection = { connected: boolean; email_address: string | null; status: string; scopes: string[]; connected_at: string | null; last_sync_at: string | null; last_error: string | null };
export type GmailSyncResult = { imported_messages: number; imported_attachments: number; duplicate_messages: number; failed_messages: { message_id: string; error: string }[]; next_page_token: string | null };
export type ReviewRequest = { id:string; case_id:string; requester:string; request_type:string; reason:string; status:string; reviewer:string|null; decision_reason:string|null; created_at:string; updated_at:string };
export type Member = { id:string; subject:string; email:string; role:string; status:string };
export type EntitlementStatus = { plan_code:string; subscription_status:string; limits:Record<string,number>; usage:Record<string,number>; remaining:Record<string,number> };
export type ProviderCapability = { provider:string; status:string; modes:string[]; detail:string };
export type WorkspaceSummary = { id:string; name:string; account_type:string; role:string; status:string };
export type ChatMessage = { id:string; role:string; content:string; citations:string[]; model:string; created_at:string };

export async function backendFetch<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${backendBaseUrl}${path}`, {
    ...init,
    signal: init.signal ?? AbortSignal.timeout(15000),
    cache: "no-store",
    headers: {
      "Content-Type": "application/json",
      ...await backendAuthHeaders(),
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
