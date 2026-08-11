"use client";

import Link from "next/link";
import { Search } from "lucide-react";
import { useMemo, useState } from "react";
import type { CaseSummary } from "@/lib/backend";

export function CasesTable({ cases }: { cases: CaseSummary[] }) {
  const [query, setQuery] = useState("");
  const [severity, setSeverity] = useState("ALL");
  const filtered = useMemo(() => cases.filter(item => {
    const matchesText = `${item.id} ${item.subject} ${item.case_type}`.toLowerCase().includes(query.toLowerCase());
    return matchesText && (severity === "ALL" || item.severity === severity);
  }), [cases, query, severity]);
  return <section className="panel data-panel">
    <div className="toolbar"><label><Search size={15}/><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Search cases" /></label><select value={severity} onChange={event => setSeverity(event.target.value)}><option value="ALL">All severities</option><option>CRITICAL</option><option>HIGH</option><option>MEDIUM</option><option>LOW</option></select><span>{filtered.length} results</span></div>
    <div className="records"><div className="record record-head"><span>Case</span><span>Subject</span><span>Status</span><span>Risk</span><span>Evidence</span></div>{filtered.map(item => <Link href={`/cases/${item.id}`} className="record" key={item.id}><strong>{item.id}</strong><span><b>{item.subject}</b><small>{item.case_type}</small></span><span className="status-pill">{item.status.replaceAll("_", " ")}</span><span className={`severity ${item.severity.toLowerCase()}`}>{item.risk_score} · {item.severity}</span><span>{item.evidence_count}</span></Link>)}</div>
    {!filtered.length && <div className="empty-state">No cases match the current filters.</div>}
  </section>;
}

