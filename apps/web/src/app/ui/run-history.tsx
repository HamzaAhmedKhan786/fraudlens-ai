"use client";
import Link from "next/link";
import { ArrowUpRight, ChevronLeft, ChevronRight, Search } from "lucide-react";
import { useState } from "react";
import type { InvestigationSummary } from "@/lib/backend";
import { utcDate } from "@/lib/dates";
export function RunHistory({ initial }: { initial: InvestigationSummary[] | null }) {
  const [query, setQuery] = useState(""), [severity, setSeverity] = useState("");
  const [page, setPage] = useState(1), [sort, setSort] = useState("created");
  const filtered = (initial ?? []).filter(row => (`${row.id} ${row.case_id}`).toLowerCase().includes(query.toLowerCase()) && (!severity || row.severity === severity)).sort((a, b) => sort === "risk" ? b.risk_score - a.risk_score : b.created_at.localeCompare(a.created_at));
  return <section className="panel"><div className="panel-head"><div><h2>Investigation run history</h2><p>Latest {initial?.length ?? "—"} recorded runs · Select a case to inspect evidence</p></div></div>
    <div className="table-toolbar"><label className="table-search"><Search size={14}/><input aria-label="Search investigation runs" placeholder="Search case or investigation ID" value={query} onChange={e => { setQuery(e.target.value); setPage(1); }}/></label><select aria-label="Investigation severity" value={severity} onChange={e => { setSeverity(e.target.value); setPage(1); }}><option value="">All risks</option>{["CRITICAL", "HIGH", "MEDIUM", "LOW"].map(x => <option key={x}>{x}</option>)}</select><select aria-label="Sort investigation runs" value={sort} onChange={e => setSort(e.target.value)}><option value="created">Latest run</option><option value="risk">Highest risk</option></select></div>
    {initial === null && <div className="inline-error" role="alert">Investigation history is unavailable. Refresh the page to reconnect.</div>}
    <div className="table-scroll"><table className="enterprise-table"><thead><tr><th>Investigation</th><th>Case</th><th>Status</th><th>Deterministic risk</th><th>Recorded</th><th>Open</th></tr></thead><tbody>{filtered.slice((page - 1) * 10, page * 10).map(row => <tr key={row.id}><td>{row.id.slice(0, 8)}</td><td><Link href={`/cases/${encodeURIComponent(row.case_id)}`}><strong>{row.case_id}</strong></Link></td><td><span className="status-badge">{row.status}</span></td><td><span className={`risk-badge ${row.severity.toLowerCase()}`}><i/>{row.risk_score} <small>{row.severity}</small></span></td><td>{utcDate(row.created_at).toLocaleString("en-GB", { timeZone: "UTC" })} UTC</td><td><Link href={`/cases/${encodeURIComponent(row.case_id)}`} aria-label={`Open case ${row.case_id}`}><ArrowUpRight size={15}/></Link></td></tr>)}</tbody></table></div>
    {!filtered.length && initial !== null && <div className="empty-state">No recorded runs match your filters.</div>}
    <div className="table-pagination"><span>{filtered.length} results · Page {page}</span><div><button disabled={page === 1} onClick={() => setPage(p => p - 1)} aria-label="Previous runs"><ChevronLeft size={15}/></button><button disabled={page * 10 >= filtered.length} onClick={() => setPage(p => p + 1)} aria-label="Next runs"><ChevronRight size={15}/></button></div></div>
  </section>;
}
