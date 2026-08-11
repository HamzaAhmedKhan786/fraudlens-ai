import { backendFetch, type AuditEntry } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function AuditPage() {
  const entries = await backendFetch<AuditEntry[]>("/audit").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="COMPLIANCE" title="Audit trail" description="Immutable operational events for case, evidence, and investigation activity."/><section className="panel data-panel"><div className="records"><div className="record audit-record record-head"><span>Action</span><span>Resource</span><span>Actor</span><span>Timestamp</span></div>{entries.map(entry => <div className="record audit-record" key={entry.id}><strong>{entry.action}</strong><span>{entry.resource_id}</span><span>{entry.actor}</span><span>{new Date(entry.created_at).toLocaleString()}</span></div>)}</div>{!entries.length && <div className="empty-state">No audit events recorded.</div>}</section></div></WorkspaceShell>;
}

