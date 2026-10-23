"use client";
import { Send, Sparkles, StickyNote } from "lucide-react";
import { useState } from "react";
import type { ChatMessage } from "@/lib/backend";
import { SafeMarkdown } from "./safe-markdown";

export function CaseCopilot({ caseId, initial }: { caseId: string; initial: ChatMessage[] }) {
  const [rows, setRows] = useState(initial), [input, setInput] = useState("");
  const [busy, setBusy] = useState(false), [message, setMessage] = useState("");
  const base = `/api/cases/${encodeURIComponent(caseId)}/chat`;
  async function ask() {
    if (input.trim().length < 2 || busy) return;
    setBusy(true); setMessage("");
    const content = input.trim();
    try {
      const response = await fetch(base, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ content }) });
      if (!response.ok) throw new Error("Copilot could not answer. Verify your model configuration and permissions.");
      const body = await response.json();
      setRows(current => [...current, { id: `local-${Date.now()}`, role: "user", content, citations: [], model: "human", created_at: new Date().toISOString() }, body]);
      setInput("");
    } catch (err) { setMessage(err instanceof Error ? err.message : "Copilot unavailable."); }
    finally { setBusy(false); }
  }
  async function feedback(id: string, rating: string) {
    const explanation = rating === "CORRECT" ? null : window.prompt("Optional explanation for the reviewer");
    try {
      const response = await fetch(`${base}/${id}/feedback`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ rating, explanation }) });
      setMessage(response.ok ? "Feedback recorded. Disputed responses are routed for review." : "Feedback could not be saved.");
    } catch { setMessage("Feedback could not be saved."); }
  }
  async function note(id: string) {
    try {
      const response = await fetch(`${base}/${id}/note`, { method: "POST" });
      setMessage(response.ok ? "Answer saved as a case note." : "A case note could not be created. Check your permissions.");
    } catch { setMessage("Case note could not be saved."); }
  }
  return <section className="panel">
    <div className="panel-head"><div><h2><Sparkles size={15}/> Investigation copilot</h2><p>Answers from this case’s evidence. Human reviewers own decisions.</p></div><span className="insight-tag">CASE SCOPED</span></div>
    <div className="copilot-conversation" aria-live="polite">{!rows.length && <div className="empty-state"><Sparkles size={25}/><h3>See the evidence more clearly</h3><p>Ask for a finding summary, inconsistencies, or missing evidence.</p></div>}{rows.map(row => <article className="notice-box" key={row.id}><strong>{row.role === "assistant" ? "FraudLens Copilot" : "You"}</strong><SafeMarkdown content={row.content}/>{!!row.citations.length && <small>Sources: {row.citations.join(", ")} · {row.model}</small>}{row.role === "assistant" && <div className="copilot-feedback"><button onClick={() => void feedback(row.id, "CORRECT")}>Correct</button><button onClick={() => void feedback(row.id, "INCORRECT")}>Incorrect</button><button onClick={() => void feedback(row.id, "FALSE_POSITIVE")}>False positive</button><button onClick={() => void feedback(row.id, "MISSING_EVIDENCE")}>Missing evidence</button><button onClick={() => void note(row.id)}><StickyNote size={11}/> Save as note</button></div>}</article>)}</div>
    <form className="copilot-controls" onSubmit={e => { e.preventDefault(); void ask(); }}><textarea value={input} onChange={e => setInput(e.target.value)} placeholder="What evidence supports the current assessment?" aria-label="Ask the case copilot" maxLength={4000}/><button className="primary" disabled={busy || input.trim().length < 2}><Send size={13}/>{busy ? "Analyzing…" : "Ask"}</button></form>
    {message && <p className="notice-box" role="status">{message}</p>}
  </section>;
}
