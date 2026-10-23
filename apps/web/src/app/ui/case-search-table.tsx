"use client";

import { ArrowDownWideNarrow, ArrowUpRight, ChevronLeft, ChevronRight, Search, SlidersHorizontal } from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";
import type { CasePage } from "@/lib/analytics-types";
import { utcDate } from "@/lib/dates";

export function CaseSearchTable({ initial, initialQuery = "", compact = false }: {
  initial: CasePage | null; initialQuery?: string; compact?: boolean;
}) {
  const [data, setData] = useState(initial);
  const [query, setQuery] = useState(initialQuery);
  const [severity, setSeverity] = useState("");
  const [status, setStatus] = useState("");
  const [sort, setSort] = useState("updated");
  const [page, setPage] = useState(1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(initial ? "" : "Case data is unavailable.");
  const [attempt, setAttempt] = useState(0);
  useEffect(() => {
    if (initial && query === initialQuery && !severity && !status && sort === "updated" && page === 1 && !attempt) {
      setData(initial); setError(""); setBusy(false);
      return;
    }
    const controller = new AbortController();
    const timer = setTimeout(async () => {
      setBusy(true);
      const params = new URLSearchParams({ q: query, sort, page: String(page), page_size: compact ? "6" : "10" });
      if (severity) params.set("severity", severity);
      if (status) params.set("status", status);
      try {
        const response = await fetch(`/api/cases/search?${params}`, { signal: controller.signal });
        if (!response.ok) throw new Error("Case data is unavailable. Please retry.");
        setData(await response.json()); setError("");
      } catch (err) {
        if (!controller.signal.aborted) setError(err instanceof Error ? err.message : "Request failed.");
      } finally { if (!controller.signal.aborted) setBusy(false); }
    }, 250);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query, severity, status, sort, page, compact, initial, initialQuery, attempt]);
  return <section className="panel enterprise-cases">
    <div className="panel-head"><div><h2>{compact ? "Recent cases" : "Case intelligence"}</h2><p>Prioritize, investigate, and review</p></div><Link href="/cases" className="text-action">All cases <ArrowUpRight size={14}/></Link></div>
    <div className="table-toolbar">
      <label className="table-search"><Search size={14}/><input aria-label="Search case table" value={query} placeholder="Search by case ID, subject, or type" onChange={e => { setQuery(e.target.value); setPage(1); }}/></label>
      <label className="table-filter"><SlidersHorizontal size={13}/><select aria-label="Filter severity" value={severity} onChange={e => { setSeverity(e.target.value); setPage(1); }}><option value="">All risks</option>{["CRITICAL", "HIGH", "MEDIUM", "LOW"].map(value => <option key={value}>{value}</option>)}</select></label>
      {!compact && <select aria-label="Filter case status" value={status} onChange={e => { setStatus(e.target.value); setPage(1); }}><option value="">All statuses</option>{["OPEN", "UNDER_REVIEW", "ESCALATED", "RESOLVED"].map(value => <option key={value}>{value}</option>)}</select>}
      <label className="table-filter"><ArrowDownWideNarrow size={13}/><select aria-label="Sort cases" value={sort} onChange={e => { setSort(e.target.value); setPage(1); }}><option value="updated">Updated</option><option value="risk">Highest risk</option><option value="created">Newest</option><option value="subject">Subject A–Z</option></select></label>
    </div>
    {error && <div role="alert" className="inline-error">{error}<button onClick={() => setAttempt(value => value + 1)}>Retry</button></div>}
    <div className="table-scroll" aria-busy={busy}><table className="enterprise-table"><thead><tr><th>Case / Subject</th><th>Type</th><th>Status</th><th>Risk</th><th>Updated</th><th><span className="sr-only">Open</span></th></tr></thead><tbody>
      {data?.items.map(item => <tr key={item.id}><td><Link href={`/cases/${encodeURIComponent(item.id)}`}><small className="case-reference">{item.id}</small><strong>{item.subject}</strong></Link></td><td>{item.case_type}</td><td><span className={`status-badge ${item.status.toLowerCase()}`}>{item.status.replaceAll("_", " ").toLowerCase()}</span></td><td><span className={`risk-badge ${item.severity.toLowerCase()}`}><i/>{item.risk_score} <small>{item.severity.toLowerCase()}</small></span></td><td><time dateTime={item.updated_at}>{utcDate(item.updated_at).toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" })}</time></td><td><Link className="table-open" aria-label={`Open ${item.id}`} href={`/cases/${encodeURIComponent(item.id)}`}><ArrowUpRight size={16}/></Link></td></tr>)}
    </tbody></table>{!error && !data?.items.length && <div className="empty-state">No cases match these filters. Create an investigation or adjust the search.</div>}</div>
    <div className="table-pagination"><span>{busy ? "Updating…" : `${data?.total ?? 0} cases`} · Page {page}</span><div><button disabled={page === 1 || busy} aria-label="Previous page" onClick={() => setPage(p => p - 1)}><ChevronLeft size={15}/></button><button disabled={!data || page * data.page_size >= data.total || busy} aria-label="Next page" onClick={() => setPage(p => p + 1)}><ChevronRight size={15}/></button></div></div>
  </section>;
}
