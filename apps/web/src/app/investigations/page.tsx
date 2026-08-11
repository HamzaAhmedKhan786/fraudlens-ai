import Link from "next/link";
import { backendFetch, type InvestigationSummary } from "@/lib/backend";
import { NewInvestigationButton } from "../ui/new-investigation";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function InvestigationsPage() {
  const rows = await backendFetch<InvestigationSummary[]>("/investigations").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="ORCHESTRATION" title="Investigations" description="Auditable agent runs, deterministic scores, and human-review outcomes." action={<NewInvestigationButton/>}/><section className="panel data-panel"><div className="records"><div className="record investigation-record record-head"><span>Investigation</span><span>Case</span><span>Status</span><span>Risk</span><span>Created</span></div>{rows.map(row => <Link href={`/cases/${row.case_id}`} className="record investigation-record" key={row.id}><strong>{row.id.slice(0,8)}</strong><span>{row.case_id}</span><span className="status-pill">{row.status}</span><span className={`severity ${row.severity.toLowerCase()}`}>{row.risk_score} · {row.severity}</span><span>{new Date(row.created_at).toLocaleString()}</span></Link>)}</div>{!rows.length && <div className="empty-state">No completed investigations yet.</div>}</section></div></WorkspaceShell>;
}

