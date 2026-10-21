"use client";

import { Mail, RefreshCw, Unplug } from "lucide-react";
import { useState } from "react";
import type { CaseSummary, GmailConnection, GmailSyncResult } from "@/lib/backend";

export function GmailConsole({ initial, cases }: { initial: GmailConnection; cases: CaseSummary[] }) {
  const [connection, setConnection] = useState(initial);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [result, setResult] = useState<GmailSyncResult | null>(null);
  const [filters, setFilters] = useState({ case_id: cases[0]?.id ?? "", sender: "", after: "", before: "", label_ids: "INBOX", has_attachment: "" });
  async function connect() {
    setBusy(true); setMessage("");
    const response = await fetch("/api/connectors/google/authorize", { method: "POST" });
    const body = await response.json();
    if (!response.ok) { setBusy(false); setMessage(body.detail ?? "Authorization failed"); return; }
    window.location.assign(body.authorization_url);
  }
  async function disconnect() {
    setBusy(true); const response = await fetch("/api/connectors/google", { method: "DELETE" }); setBusy(false);
    if (response.ok) setConnection({ connected: false, email_address: null, status: "NOT_CONNECTED", scopes: [], connected_at: null, last_sync_at: null, last_error: null });
    else setMessage("Disconnect failed");
  }
  async function sync() {
    setBusy(true); setMessage(""); setResult(null);
    const payload = { ...filters, label_ids: filters.label_ids.split(",").map(value => value.trim()).filter(Boolean), sender: filters.sender || null, after: filters.after ? filters.after.replaceAll("-", "/") : null, before: filters.before ? filters.before.replaceAll("-", "/") : null, has_attachment: filters.has_attachment === "" ? null : filters.has_attachment === "true", max_messages: 25 };
    const response = await fetch("/api/connectors/google/sync", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const body = await response.json(); setBusy(false);
    if (!response.ok) { setMessage(body.detail ?? "Sync failed"); return; }
    setResult(body); setMessage(body.failed_messages.length ? `Gmail sync finished with ${body.failed_messages.length} failure(s). No failed message was imported.` : "Gmail synchronization completed. Imported evidence is attached to the selected case; run an investigation there to update its risk score.");
  }
  return <section className="panel connector-card"><div className="connector-title"><span><Mail size={22}/></span><div><h2>Gmail</h2><p>Read-only OAuth ingestion into an existing case.</p></div><em className={connection.connected ? "connected" : "offline"}>{connection.status.replaceAll("_", " ")}</em></div>
    {!connection.connected ? <div className="connector-empty"><p>FraudLens requests <code>gmail.readonly</code>. Your password is never shared or stored.</p><button className="primary" onClick={connect} disabled={busy}>Connect Gmail</button></div> : <>
      <div className="connector-account"><strong>{connection.email_address}</strong><span>Last sync: {connection.last_sync_at ? new Date(connection.last_sync_at).toLocaleString() : "Never"}</span><button onClick={disconnect} disabled={busy}><Unplug size={14}/> Disconnect & revoke</button></div>
      <div className="connector-filters"><label>Existing case<select value={filters.case_id} onChange={event => setFilters({...filters, case_id:event.target.value})}><option value="">Select a case</option>{cases.map(item => <option value={item.id} key={item.id}>{item.id} · {item.subject}</option>)}</select></label><label>Labels<input value={filters.label_ids} onChange={event => setFilters({...filters, label_ids:event.target.value})} placeholder="INBOX or SPAM"/></label><label>Sender<input value={filters.sender} onChange={event => setFilters({...filters, sender:event.target.value})} placeholder="supplier@example.com"/></label><label>After<input type="date" value={filters.after} onChange={event => setFilters({...filters, after:event.target.value})}/></label><label>Before<input type="date" value={filters.before} onChange={event => setFilters({...filters, before:event.target.value})}/></label><label>Attachments<select value={filters.has_attachment} onChange={event => setFilters({...filters, has_attachment:event.target.value})}><option value="">Any</option><option value="true">Required</option><option value="false">None</option></select></label></div>
      <button className="primary connector-sync" onClick={sync} disabled={busy || filters.case_id.length < 3}><RefreshCw size={15}/>{busy ? "Synchronizing…" : "Import next 25 messages"}</button>
    </>}{message && <p className="connector-message">{message}</p>}{result && <><div className="sync-result"><span>{result.imported_messages} messages</span><span>{result.imported_attachments} attachments</span><span>{result.duplicate_messages} duplicates</span><span>{result.failed_messages.length} failed</span></div>{result.failed_messages.length > 0 && <div className="connector-message"><strong>Failure details</strong><ul>{[...new Set(result.failed_messages.map(item => item.error))].slice(0, 5).map(error => <li key={error}>{error}</li>)}</ul></div>}</>}</section>;
}
