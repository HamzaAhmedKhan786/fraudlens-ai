"use client";

import { Activity, ArrowRight, ArrowUpRight, CalendarDays, FileCheck2, FolderOpen, Globe2, Layers, RefreshCw, ShieldAlert, ShieldCheck, Sparkles, Workflow } from "lucide-react";
import Link from "next/link";
import dynamic from "next/dynamic";
import { useState } from "react";
import type { Overview, CasePage } from "@/lib/analytics-types";
import type { AgentStatus } from "@/lib/backend";
import { utcDate } from "@/lib/dates";
import { NewInvestigationButton } from "./new-investigation";
import { RiskDonut, TrendChart } from "./analytics-charts";
import { CaseSearchTable } from "./case-search-table";

const WorldRiskMap = dynamic(() => import("./world-risk-map"), {
  ssr: false,
  loading: () => <div className="empty-state" role="status">Loading world basemap…</div>,
});

export function CommandCenter({ initial, cases, agents, analyticsOnly = false }: {
  initial: Overview | null; cases: CasePage | null; agents: AgentStatus[] | null; analyticsOnly?: boolean;
}) {
  const [data, setData] = useState(initial);
  const [days, setDays] = useState(initial?.days ?? 7);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initial ? "" : "Analytics are temporarily unavailable.");
  async function load(period: number) {
    setBusy(true); setDays(period);
    try {
      const response = await fetch(`/api/analytics?days=${period}`);
      if (!response.ok) throw new Error("Analytics could not be refreshed. Last available data remains visible.");
      setData(await response.json()); setError("");
    } catch (err) { setError(err instanceof Error ? err.message : "Analytics unavailable."); }
    finally { setBusy(false); }
  }
  const metrics = [
    { label: "Total investigations", value: data?.summary.total_investigations, detail: "Recorded agent runs", icon: Workflow, href: "/investigations", tone: "teal" },
    { label: "Open cases", value: data?.summary.open_cases, detail: "Awaiting investigation or review", icon: FolderOpen, href: "/cases", tone: "cyan" },
    { label: "High / critical cases", value: data?.summary.high_risk_cases, detail: "Deterministic risk indicators", icon: ShieldAlert, href: "/cases", tone: "orange" },
    { label: "Evidence files analyzed", value: data?.summary.evidence_processed, detail: "Successfully processed uploads", icon: FileCheck2, href: "/uploads", tone: "violet" },
    { label: "Average risk score", value: data?.summary.average_risk, detail: "Across retained cases · /100", icon: Activity, href: "/analytics", tone: "teal" },
  ];
  const latest = data?.latest;
  const finding = latest?.report.findings[0];
  return <div className="content command-center" aria-busy={busy}>
    <div className="heading-row"><div><p className="eyebrow"><span/> FRAUD INTELLIGENCE WORKSPACE</p><h1>{analyticsOnly ? "Risk analytics" : "Fraud intelligence command center"}</h1><p>A clear view of risk. A faster path from evidence to decision.</p></div><div className="heading-actions"><button className="secondary icon-action" onClick={() => void load(days)} disabled={busy} aria-label="Refresh dashboard"><RefreshCw size={15}/></button><NewInvestigationButton/></div></div>
    <div className="dashboard-context"><div><span className={`data-indicator ${data ? "" : "unavailable"}`}/>{data?.data_source === "DEMO_DATASET" ? "Development sample dataset" : data ? "Workspace data" : "Data unavailable"}<span className="context-divider">|</span><span>{data ? `Updated ${utcDate(data.as_of).toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", timeZone: "UTC" })} UTC` : "Connect to the API to load analytics"}</span></div><label><CalendarDays size={14}/><select aria-label="Analytics date range" value={days} disabled={busy} onChange={e => void load(Number(e.target.value))}><option value={7}>Last 7 days</option><option value={30}>Last 30 days</option><option value={90}>Last 90 days</option></select></label></div>
    {error && <div role="alert" className="inline-error">{error}<button onClick={() => void load(days)}>Retry</button></div>}
    <section className="kpi-grid">{metrics.map(({ label, value, detail, icon: Icon, href, tone }) => <Link href={href} className={`panel kpi-card ${tone}`} key={label}><div className="kpi-label"><span className="kpi-icon"><Icon size={16}/></span><span>{label}</span><ArrowUpRight size={13}/></div><strong>{value === undefined ? "—" : value.toLocaleString("en-GB")}</strong><div className="kpi-foot"><span>{detail}</span><div className="kpi-rule"/></div></Link>)}</section>
    <div className="analytics-grid">
      <section className="panel geography-panel"><div className="panel-head"><div><h2>Global risk intelligence</h2><p>World basemap · Verified risk data when available</p></div><span className="quiet-label"><Globe2 size={13}/> All regions</span></div><WorldRiskMap reason={data?.geography.reason ?? "Connect the API to check geographic risk data availability."}/><div className="map-legend"><span><i className="low"/>Low</span><span><i className="medium"/>Medium</span><span><i className="high"/>High</span><span><i className="critical"/>Critical</span><small>Risk layer inactive</small></div></section>
      <section className="panel distribution-panel"><div className="panel-head"><div><h2>Cases by risk level</h2><p>Persisted deterministic assessment</p></div><ShieldCheck size={16}/></div>{data ? <RiskDonut distribution={data.distribution} threshold={data.critical_threshold}/> : <div className="empty-state">Risk distribution unavailable</div>}</section>
      <section className="panel ai-insight-panel"><div className="panel-head"><div><h2><Sparkles size={15}/> Risk intelligence</h2><p>Latest recorded investigation</p></div><span className="insight-tag">EVIDENCE FIRST</span></div><div className="insight-content">{latest ? <><span className={`risk-badge ${latest.report.risk.severity.toLowerCase()}`}><i/>{latest.report.risk.severity} · {latest.report.risk.score}/100</span><h3>{finding?.title ?? latest.subject}</h3><p>{finding?.explanation ?? "No configured fraud indicators were detected. Human validation remains necessary."}</p><div className="confidence-label"><span>{finding ? "Indicator confidence" : "Case status"}</span><strong>{finding ? `${Math.round(finding.confidence * 100)}%` : latest.status.replaceAll("_", " ")}</strong></div>{finding && <div className="confidence-track"><i style={{ width: `${finding.confidence * 100}%` }}/></div>}<div className="insight-evidence">{finding?.evidence_ids.slice(0, 2).map(id => <span key={id}><Layers size={12}/>{id}</span>)}</div><small className="review-label"><ShieldCheck size={12}/>{latest.disposition ? latest.disposition.replaceAll("_", " ") : "Human review required"}</small><Link className="insight-link" href={`/cases/${encodeURIComponent(latest.id)}`}>Open investigation <ArrowUpRight size={14}/></Link></> : <div className="empty-state"><Sparkles size={26}/><h3>Ready for your first investigation</h3><p>Findings and cited explanations appear after an analysis completes.</p></div>}</div></section>
      <section className="panel trend-panel"><div className="panel-head"><div><h2>Investigation activity</h2><p>Daily recorded events · {days} days</p></div><span className="quiet-label"><Activity size={13}/> UTC</span></div>{data ? <TrendChart data={data.trend}/> : <div className="empty-state">Activity history unavailable</div>}</section>
    </div>
    <div className="operations-grid"><CaseSearchTable initial={cases} compact/><section className="panel activity-panel"><div className="panel-head"><div><h2>Workspace activity</h2><p>Most recent audit events</p></div><Link href="/audit" className="text-action">View all <ArrowUpRight size={13}/></Link></div><div className="activity-list">{data?.activity.map(event => <article key={event.id}><i/><div><strong>{event.action.replaceAll(".", " · ").replaceAll("_", " ")}</strong><span>{event.resource_id}</span><small>{utcDate(event.created_at).toLocaleString("en-GB", { day: "numeric", month: "short", hour: "2-digit", minute: "2-digit", timeZone: "UTC" })} UTC</small></div></article>)}{!data?.activity.length && <div className="empty-state">Recorded activity will appear here.</div>}</div><Link href="/reviews" className="queue-summary"><ShieldCheck size={16}/><span>Pending human reviews</span><strong>{data?.summary.pending_reviews ?? "—"}</strong><ArrowUpRight size={14}/></Link></section></div>
    <div className="readiness-grid">
      <section className="panel"><div className="panel-head"><div><h2>Agent readiness</h2><p>Configured capabilities, not live health probes</p></div><Link href="/agents" className="text-action">Agents <ArrowUpRight size={13}/></Link></div><div className="readiness-list">{agents?.map(agent => <div key={agent.id}><span><ShieldCheck size={14}/>{agent.name}</span><small className={agent.status === "ONLINE" ? "configured" : ""}>{agent.status === "ONLINE" ? "Configured" : "Standby"}</small></div>)}{!agents && <div className="empty-state">Agent configuration unavailable</div>}</div></section>
      <section className="panel"><div className="panel-head"><div><h2>Evidence processing</h2><p>Current upload states</p></div><Link href="/uploads" className="text-action">Evidence <ArrowUpRight size={13}/></Link></div><div className="processing-list">{data?.processing.map(item => <div key={item.status}><span>{item.status.replaceAll("_", " ").toLowerCase()}</span><strong>{item.count}</strong></div>)}{!data?.processing.length && <div className="empty-state">No upload records in this workspace.</div>}</div></section>
      <section className="panel"><div className="panel-head"><div><h2>Investigation categories</h2><p>Case types across your workspace</p></div></div><div className="category-list">{data?.categories.map(item => <div key={item.name}><span>{item.name}</span><strong>{item.count}</strong><div><i style={{ width: `${data.summary.total_cases ? item.count / data.summary.total_cases * 100 : 0}%` }}/></div></div>)}{!data?.categories.length && <div className="empty-state">Categories populate as cases are created.</div>}</div></section>
    </div>
  </div>;
}
