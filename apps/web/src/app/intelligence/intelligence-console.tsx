"use client";

import { Globe2, RefreshCw, ShieldCheck } from "lucide-react";
import { useState } from "react";
import type { PublicIntelligence } from "@/lib/backend";

export function IntelligenceConsole({ initialItems }: { initialItems: PublicIntelligence[] }) {
  const [items, setItems] = useState(initialItems);
  const [domain, setDomain] = useState("");
  const [state, setState] = useState<"idle" | "loading" | "error">("idle");
  const [message, setMessage] = useState("");
  async function lookup(event: React.FormEvent) {
    event.preventDefault(); setState("loading"); setMessage("");
    const response = await fetch("/api/intelligence", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ domain }) });
    const data = await response.json();
    if (!response.ok) { setState("error"); setMessage(data.detail ?? "Lookup failed"); return; }
    setItems(current => [data as PublicIntelligence, ...current]); setDomain(""); setState("idle");
  }
  return <>
    <section className="panel intel-lookup"><div><Globe2 size={22}/><h2>Live domain registration lookup</h2><p>Fetch factual registration metadata from the public RDAP network. Results are persisted with provider, source URL, and fetch time.</p></div><form onSubmit={lookup}><input aria-label="Domain" value={domain} onChange={event => setDomain(event.target.value)} placeholder="example.com" required pattern="[A-Za-z0-9.-]+"/><button className="primary" disabled={state === "loading"}><RefreshCw size={15}/>{state === "loading" ? "Fetching…" : "Fetch live facts"}</button></form>{message && <p className="form-error">{message}</p>}</section>
    <div className="provenance-note"><ShieldCheck size={16}/><span>RDAP facts provide context only. FraudLens does not label a person or domain fraudulent solely from registration metadata.</span></div>
    <section className="intel-grid">{items.map(item => <article className="panel intel-card" key={item.id}><div className="feature-top"><span className="status-dot healthy"/><em>PUBLIC SOURCE</em><b>{new Date(item.fetched_at).toLocaleString()}</b></div><h2>{item.indicator}</h2><p>{item.provider}</p><dl><dt>Registered</dt><dd>{String(item.facts.registration_date ?? "Not disclosed")}</dd><dt>Expires</dt><dd>{String(item.facts.expiration_date ?? "Not disclosed")}</dd><dt>Nameservers</dt><dd>{Array.isArray(item.facts.nameservers) ? item.facts.nameservers.join(", ") || "Not disclosed" : "Not disclosed"}</dd></dl><a href={item.source_uri} target="_blank" rel="noreferrer">Open authoritative response →</a></article>)}{!items.length && <div className="panel empty-intel"><Globe2 size={28}/><h2>No public facts stored yet</h2><p>Run a lookup above. Nothing on this screen is seeded or invented.</p></div>}</section>
  </>;
}
