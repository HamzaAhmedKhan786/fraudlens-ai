export type CaseRow = {
  id: string; subject: string; case_type: string; status: string;
  risk_score: number; severity: string; assignee: string | null;
  updated_at: string; evidence_count: number;
};
export type CasePage = { items: CaseRow[]; total: number; page: number; page_size: number };
export type Finding = {
  id: string; title: string; explanation: string; confidence: number; severity: string;
  evidence_ids: string[]; agent?: string;
};
export type Report = {
  summary: string; findings: Finding[]; risk: { score: number; severity: string };
  requires_human_review: boolean;
  agent_trace: { agent: string; status: string; duration_ms: number; finding_count: number }[];
};
export type Overview = {
  data_source: string; as_of: string; days: number; critical_threshold: number;
  summary: { total_cases: number; open_cases: number; high_risk_cases: number;
    average_risk: number; total_investigations: number; evidence_processed: number;
    pending_reviews: number };
  distribution: { severity: string; count: number }[];
  trend: { date: string; created: number; completed: number; high_risk: number; evidence: number }[];
  processing: { status: string; count: number }[];
  categories: { name: string; count: number }[];
  latest: { id: string; subject: string; status: string; disposition: string | null; report: Report } | null;
  activity: { id: string; action: string; resource_id: string; created_at: string; actor: string }[];
  geography: { available: boolean; reason: string };
};
export type SessionInfo = {
  name: string; roles: string[]; tenant_id: string; workspace: string; development: boolean;
};
