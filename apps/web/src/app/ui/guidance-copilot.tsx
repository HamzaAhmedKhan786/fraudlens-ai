"use client";

import { ArrowUpRight, BookOpen, Check, ChevronRight, LoaderCircle, MessageCircle, Send, Sparkles, ThumbsDown, ThumbsUp, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { SafeMarkdown } from "./safe-markdown";

type Citation = { document_id: string; section: string; route: string; revision: string };
type Message = { role: "assistant" | "user"; content: string; path?: string | null; citations?: Citation[]; feedback?: boolean };
const welcome: Message = {
  role: "assistant", content: "Welcome to FraudLens. I can help you find your way, understand risk scores, and make the most of your workspace.",
};
const routeQuestions: Record<string, string[]> = {
  "/uploads": ["Which file types can I upload?", "Why was my file rejected?", "Does uploading make a file suspicious?"],
  "/connectors": ["How do I connect Gmail?", "Who can access my email evidence?", "What can the case copilot do?"],
  "/billing": ["What does my subscription include?", "What can the product guide do?"],
  "/cases": ["How do I start an investigation?", "Does Critical mean confirmed fraud?", "What is the case copilot?"],
};

export function GuidanceCopilot() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [messages, setMessages] = useState<Message[]>([welcome]);
  const [error, setError] = useState("");
  const [scope, setScope] = useState<string | null>(null);
  const dialog = useRef<HTMLDialogElement>(null);
  const end = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const publicPage = ["/login", "/signup", "/pricing"].some(route => pathname.startsWith(route));
  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/session", { signal: controller.signal }).then(r => r.ok ? r.json() : null).then(session => {
      if (!session) return;
      const key = `fraudlens-guide:${session.tenant_id}:${session.name}`;
      setScope(key);
      try {
        const stored = sessionStorage.getItem(key);
        if (stored) setMessages((JSON.parse(stored) as Message[]).slice(-30));
      } catch { /* Session storage may be disabled. */ }
    }).catch(() => {});
    return () => controller.abort();
  }, [publicPage]);
  useEffect(() => {
    if (scope) { try { sessionStorage.setItem(scope, JSON.stringify(messages.slice(-30))); } catch { /* Optional persistence. */ } }
  }, [scope, messages]);
  useEffect(() => {
    const show = () => setOpen(true);
    const keyboard = (event: KeyboardEvent) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "/") { event.preventDefault(); show(); }
    };
    window.addEventListener("fraudlens:help", show); window.addEventListener("keydown", keyboard);
    return () => { window.removeEventListener("fraudlens:help", show); window.removeEventListener("keydown", keyboard); };
  }, []);
  useEffect(() => {
    if (open && !publicPage) { dialog.current?.showModal(); inputRef.current?.focus(); }
    else dialog.current?.close();
  }, [open, publicPage]);
  useEffect(() => { end.current?.scrollIntoView({ block: "nearest" }); }, [messages, busy]);
  async function send(question = input) {
    const content = question.trim();
    if (content.length < 2 || busy) return;
    setInput(""); setBusy(true); setError("");
    setMessages(rows => [...rows, { role: "user", content }]);
    try {
      const response = await fetch("/api/copilot/guide", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ content, current_path: pathname }),
      });
      if (!response.ok) throw new Error("The guide could not answer. Check your connection or try again.");
      const body = await response.json();
      setMessages(rows => [...rows, { role: "assistant", content: body.content, path: body.suggested_path, citations: body.citations }]);
    } catch (err) { setError(err instanceof Error ? err.message : "The guide is unavailable."); }
    finally { setBusy(false); inputRef.current?.focus(); }
  }
  async function feedback(index: number, helpful: boolean) {
    const message = messages[index];
    try {
      const response = await fetch("/api/copilot/guide/feedback", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ helpful, document_ids: message.citations?.map(c => c.document_id) ?? [], revisions: message.citations?.map(c => c.revision) ?? [] }),
      });
      if (!response.ok) throw new Error();
      setMessages(rows => rows.map((row, i) => i === index ? { ...row, feedback: helpful } : row));
    } catch { setError("Feedback could not be saved. Please retry."); }
  }
  if (publicPage) return null;
  const suggestions = routeQuestions[pathname] ?? routeQuestions["/cases"];
  return <>
    <button className="help-launcher" aria-label="Open AI help assistant" aria-haspopup="dialog" onClick={() => setOpen(true)}><Sparkles size={19}/><span>Ask FraudLens</span><kbd>⌘ /</kbd></button>
    <dialog className="help-drawer" ref={dialog} onCancel={() => setOpen(false)} onClose={() => setOpen(false)} aria-labelledby="guide-title">
      <div className="help-header"><div className="help-avatar"><Sparkles size={22}/></div><div><h2 id="guide-title">FraudLens Assistant</h2><span><i/> Your product guide</span></div><button aria-label="Close AI help" onClick={() => setOpen(false)}><X size={19}/></button></div>
      <div className="help-context"><BookOpen size={13}/> Documentation answers <ChevronRight size={12}/><span>{pathname === "/" ? "Command center" : pathname.split("/")[1]}</span></div>
      <div className="help-body">
        <div className="help-intro"><span>CLARITY AT EVERY STEP</span><h3>What can I help<br/>you discover?</h3><p>Find answers grounded in your FraudLens documentation.</p></div>
        <div className="help-suggestions">{suggestions.map(question => <button key={question} disabled={busy} onClick={() => void send(question)}><MessageCircle size={14}/><span>{question}</span><ArrowUpRight size={13}/></button>)}</div>
        <div className="help-conversation" aria-live="polite" aria-relevant="additions">{messages.map((message, index) => <article className={`help-message ${message.role}`} key={index}>
          <div className="help-message-label">{message.role === "assistant" ? <><Sparkles size={12}/> FraudLens</> : "You"}</div>
          <SafeMarkdown content={(message.citations ?? []).reduce((text, citation, i) => text.replaceAll(`[${citation.document_id}#${citation.section}]`, `[${i + 1}]`), message.content)}/>
          {!!message.citations?.length && <details className="help-sources"><summary><BookOpen size={12}/> {message.citations.length} documentation {message.citations.length === 1 ? "source" : "sources"}</summary>{message.citations.map(citation => <div key={citation.document_id + citation.section}><strong>{citation.section}</strong><small>{citation.document_id} · {citation.revision}</small></div>)}</details>}
          {message.path?.startsWith("/") && <Link className="help-route" href={message.path} onClick={() => setOpen(false)}>Open relevant page <ArrowUpRight size={13}/></Link>}
          {!!message.citations?.length && <div className="help-feedback">{message.feedback === undefined ? <><span>Was this helpful?</span><button aria-label="Helpful answer" onClick={() => void feedback(index, true)}><ThumbsUp size={13}/></button><button aria-label="Unhelpful answer" onClick={() => void feedback(index, false)}><ThumbsDown size={13}/></button></> : <span><Check size={12}/> Feedback saved</span>}</div>}
        </article>)}{busy && <div className="help-thinking" role="status"><LoaderCircle size={14}/> Finding relevant documentation…</div>}<div ref={end}/></div>
      </div>
      {error && <div className="inline-error" role="alert">{error}</div>}
      <form className="help-composer" onSubmit={event => { event.preventDefault(); void send(); }}><textarea ref={inputRef} value={input} onChange={event => setInput(event.target.value)} onKeyDown={event => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void send(); } }} maxLength={4000} placeholder="Ask about FraudLens…" aria-label="Message the product guide"/><button disabled={busy || input.trim().length < 2} aria-label="Send guide message" type="submit"><Send size={17}/></button></form>
      <div className="help-footnote"><ShieldLabel/> Product guidance · Case evidence stays in the case copilot</div>
    </dialog>
  </>;
}
function ShieldLabel() { return <BookOpen size={11}/>; }
