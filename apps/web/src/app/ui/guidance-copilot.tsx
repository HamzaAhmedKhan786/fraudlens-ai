"use client";

import { Bot, ExternalLink, Send, X } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

type Citation = { document_id: string; section: string; route: string; revision: string };
type Message = { role: "assistant" | "user"; content: string; path?: string | null; citations?: Citation[] };

export function GuidanceCopilot() {
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<Message[]>([{
    role: "assistant",
    content: "Hi—I'm your FraudLens guide. Ask how to upload evidence, connect email, start an investigation, review findings, or manage a workspace.",
  }]);

  async function send() {
    const content = input.trim();
    if (!content || busy) return;
    setInput("");
    setBusy(true);
    setMessages(rows => [...rows, { role: "user", content }]);
    try {
      const response = await fetch("/api/copilot/guide", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content }),
      });
      const body = await response.json();
      setMessages(rows => [...rows, {
        role: "assistant",
        content: response.ok ? body.content : body.detail,
        path: body.suggested_path,
        citations: body.citations,
      }]);
    } catch {
      setMessages(rows => [...rows, {
        role: "assistant", content: "The guide is temporarily unavailable.",
      }]);
    } finally {
      setBusy(false);
    }
  }

  return <div className={`guide-copilot ${open ? "open" : ""}`}>
    {open && <section className="guide-panel" aria-label="FraudLens guidance assistant">
      <header><span><Bot size={19}/><strong>FraudLens Guide</strong></span><button onClick={() => setOpen(false)} aria-label="Close guide"><X size={18}/></button></header>
      <p className="guide-safety">Product guidance only. Decisions remain with deterministic detectors and authorized reviewers.</p>
      <div className="guide-messages">{messages.map((message, index) => <article className={message.role} key={`${message.role}-${index}`}><strong>{message.role === "user" ? "You" : "Guide"}</strong><p>{message.content}</p>{message.citations?.length ? <small>Sources: {message.citations.map(citation => `${citation.document_id} · ${citation.section}`).join("; ")}</small> : null}{message.path && <Link href={message.path}>Open relevant page <ExternalLink size={13}/></Link>}</article>)}</div>
      <div className="guide-input"><textarea value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); } }} maxLength={4000} placeholder="How can I…"/><button disabled={busy || !input.trim()} onClick={() => void send()} aria-label="Send"><Send size={17}/></button></div>
    </section>}
    <button className="guide-launcher" onClick={() => setOpen(value => !value)} aria-label={open ? "Close FraudLens Guide" : "Open FraudLens Guide"}><Bot size={23}/><span>{open ? "Close" : "Ask FraudLens"}</span></button>
  </div>;
}
