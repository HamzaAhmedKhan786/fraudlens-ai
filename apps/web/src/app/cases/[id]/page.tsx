import Link from "next/link";
import { backendFetch, type CaseDetail, type ChatMessage } from "@/lib/backend";
import { CaseCopilot } from "../../ui/case-copilot";
import { DeleteInvestigationButton } from "../../ui/delete-investigation-button";
import { CaseWorkflow } from "../../ui/case-workflow";
import { SectionHeader, WorkspaceShell } from "../../ui/workspace-shell";

export default async function CasePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const item = await backendFetch<CaseDetail>(`/cases/${encodeURIComponent(id)}`).catch(() => null);
  if (!item) return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="CASE" title="Case unavailable" description="The case does not exist or the API is unavailable."/><Link href="/cases" className="primary inline-action">Back to cases</Link></div></WorkspaceShell>;
  const chat=await backendFetch<ChatMessage[]>(`/cases/${encodeURIComponent(id)}/chat`).catch(()=>[]);
  return <WorkspaceShell><div className="content section-page">
    <SectionHeader eyebrow="CASE INVESTIGATION" title={item.subject} description={`${item.id} · ${item.case_type} · ${item.status.replaceAll("_", " ")}${item.disposition ? ` · ${item.disposition.replaceAll("_", " ")}` : ""}`}/>
    <CaseWorkflow item={item}/>
    <DeleteInvestigationButton caseId={item.id}/>
    <CaseCopilot caseId={item.id} initial={chat}/>
    <section className="detail-grid"><article className="panel score-card"><span>DETERMINISTIC RISK</span><strong>{item.risk_score}</strong><em className={`severity ${item.severity.toLowerCase()}`}>{item.severity}</em><a href={`/api/cases/${encodeURIComponent(item.id)}/report`}>Export report</a></article><article className="panel"><div className="panel-head"><div><h2>Investigation summary</h2><p>Evidence-grounded narrative</p></div></div><div className="panel-body"><p>{item.latest_report?.summary ?? "No investigation report has been generated yet."}</p></div></article></section>
    <section className="panel data-panel"><div className="panel-head"><div><h2>Evidence</h2><p>{item.evidence.length} immutable evidence records</p></div></div><div className="cards-grid">{item.evidence.map(e => <article className="mini-card" key={e.id}><span>{e.kind.toUpperCase()}</span><strong>{e.source}</strong><small>{e.id}</small><pre>{JSON.stringify(e.attributes, null, 2)}</pre></article>)}</div></section>
    {item.latest_report && <section className="panel data-panel"><div className="panel-head"><div><h2>Findings</h2><p>{item.latest_report.findings.length} validated indicators</p></div></div><div className="cards-grid">{item.latest_report.findings.map(f => <article className="mini-card" key={f.id}><span>{f.severity} · {(f.confidence*100).toFixed(0)}%</span><strong>{f.title}</strong><p>{f.explanation}</p><small>Citations: {f.evidence_ids.join(", ")}</small></article>)}</div></section>}
  </div></WorkspaceShell>;
}
