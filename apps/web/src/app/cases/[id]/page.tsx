import Link from "next/link";
import type { CSSProperties } from "react";
import { ArrowLeft, Download, FileCheck2, ShieldCheck } from "lucide-react";
import { backendFetch, type AuditEntry, type CaseDetail, type ChatMessage } from "@/lib/backend";
import { utcDate } from "@/lib/dates";
import { CaseCopilot } from "../../ui/case-copilot";
import { DeleteInvestigationButton } from "../../ui/delete-investigation-button";
import { CaseWorkflow } from "../../ui/case-workflow";
import { CaseActions } from "../../ui/case-actions";
import { SectionHeader, WorkspaceShell } from "../../ui/workspace-shell";
import { SafeMarkdown } from "../../ui/safe-markdown";

export default async function CasePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = await backendFetch<CaseDetail>(`/cases/${encodeURIComponent(id)}`).catch(() => null);
  if (!item) return <WorkspaceShell><div className="content"><SectionHeader eyebrow="INVESTIGATION" title="Case unavailable" description="The case could not be loaded. Check the link, workspace, and service availability."/><Link href="/cases" className="primary inline-action">Back to cases</Link></div></WorkspaceShell>;
  const [chat, audit] = await Promise.all([
    backendFetch<ChatMessage[]>(`/cases/${encodeURIComponent(id)}/chat`).catch(() => []),
    backendFetch<AuditEntry[]>(`/audit?resource_id=${encodeURIComponent(id)}`).catch(() => null),
  ]);
  return <WorkspaceShell><div className="content section-page">
    <Link href="/cases" className="text-action"><ArrowLeft size={13}/> All investigations</Link>
    <div style={{ marginTop: 18 }}><SectionHeader eyebrow={`INVESTIGATION / ${item.id}`} title={item.subject} description={`${item.case_type} · Created ${utcDate(item.created_at).toLocaleDateString("en-GB", { timeZone: "UTC" })}`}/></div>
    <nav className="case-anchor-nav" aria-label="Investigation sections"><a href="#case-overview">Overview</a><a href="#evidence">Evidence ({item.evidence.length})</a><a href="#findings">Findings</a><a href="#case-copilot">AI copilot</a><a href="#case-workflow">Review & notes</a></nav>
    <div className="case-detail-layout">
      <div className="case-detail-main">
        <section className="panel" id="case-overview"><div className="panel-head"><div><h2>Investigation overview</h2><p>Deterministic risk · Evidence-linked reasoning</p></div><ShieldCheck size={17}/></div><div className="case-overview-body"><div className={`case-score ${item.severity.toLowerCase()}`} style={{ "--score": item.risk_score } as CSSProperties}><div><strong>{item.risk_score}</strong><small>of 100</small></div></div><div><div className="case-meta"><span className={`risk-badge ${item.severity.toLowerCase()}`}><i/>{item.severity}</span><span className={`status-badge ${item.status.toLowerCase()}`}>{item.status.replaceAll("_", " ")}</span></div><h2>{item.disposition ? item.disposition.replaceAll("_", " ") : "Awaiting human determination"}</h2><p>Risk indicators inform review. A score alone does not confirm fraud.</p></div></div><div className="panel-body"><SafeMarkdown content={item.latest_report?.summary ?? "No analysis report yet. Add evidence and select Run analysis to generate findings."}/></div></section>
        <section className="panel" id="evidence"><div className="panel-head"><div><h2>Evidence library</h2><p>{item.evidence.length} retained records</p></div><Link href="/uploads" className="text-action"><FileCheck2 size={13}/> Add evidence</Link></div><div className="evidence-cards">{item.evidence.map(e => <article id={e.id} className="mini-card" key={e.id}><span>{e.kind.toUpperCase()}</span><strong>{e.source}</strong><small>{e.id}</small><details><summary>View extracted metadata</summary><pre>{JSON.stringify(e.attributes, null, 2)}</pre></details></article>)}</div>{!item.evidence.length && <div className="empty-state">Add an email, document, image, or supported evidence file to begin.</div>}</section>
        <section className="panel" id="findings"><div className="panel-head"><div><h2>Findings & explanations</h2><p>{item.latest_report?.findings.length ?? 0} recorded indicators</p></div></div><div className="finding-list">{item.latest_report?.findings.map(f => <article className="finding-card" key={f.id}><span className={`risk-badge ${f.severity.toLowerCase()}`}><i/>{f.severity} · {Math.round(f.confidence * 100)}% confidence</span><h3>{f.title}</h3><p>{f.explanation}</p><small>Evidence: {f.evidence_ids.map(eid => <a href={`#${encodeURIComponent(eid)}`} key={eid}>{eid} </a>)}</small></article>)}</div>{!item.latest_report?.findings.length && <div className="empty-state">No findings recorded. Check the latest analysis status and available detectors.</div>}</section>
        <div id="case-copilot"><CaseCopilot caseId={item.id} initial={chat}/></div>
        <div id="case-workflow"><CaseWorkflow item={item}/></div>
      </div>
      <aside className="case-detail-side"><CaseActions caseId={item.id}/>
        <section className="panel"><div className="panel-head"><div><h2>Agent execution</h2><p>Latest recorded analysis run</p></div></div><div className="execution-list">{item.latest_report?.agent_trace?.map((trace, i) => <div key={trace.agent + i}><span>{trace.agent}</span><span className="status-badge">{trace.status}</span><small>{trace.duration_ms} ms · {trace.finding_count} findings</small></div>)}</div>{!item.latest_report && <div className="empty-state">No agent execution recorded.</div>}</section>
        <section className="panel"><div className="panel-head"><div><h2>Investigation timeline</h2><p>Audit history for this case</p></div></div><div className="case-timeline">{audit?.slice(0, 10).map(event => <p key={event.id}><strong>{event.action.replaceAll(".", " · ")}</strong><small>{event.actor} · {utcDate(event.created_at).toLocaleString("en-GB", { timeZone: "UTC" })} UTC</small></p>)}{!audit?.length && <p>{audit ? "No audit events for this case." : "Audit history temporarily unavailable."}</p>}</div></section>
        <section className="panel"><div className="panel-head"><div><h2>Report & retention</h2><p>Reviewable records for your investigation</p></div></div><div className="case-actions"><a href={`/api/cases/${encodeURIComponent(item.id)}/report`}><Download size={13}/>Export report</a></div><DeleteInvestigationButton caseId={item.id}/></section>
      </aside>
    </div>
  </div></WorkspaceShell>;
}
