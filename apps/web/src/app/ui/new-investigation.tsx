"use client";

import { Sparkles, X } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

const templates = [
  { id: "phishing", label: "Email phishing & spoofing", type: "Email phishing", title: "Suspicious email investigation" },
  { id: "bec", label: "Business Email Compromise", type: "BEC", title: "Business email compromise investigation" },
  { id: "document", label: "Invoice & document fraud", type: "Invoice + document", title: "Invoice or document verification" },
  { id: "url", label: "Suspicious URLs & attachments", type: "URL + attachment", title: "Suspicious link or attachment" },
  { id: "identity", label: "Identity verification", type: "Identity", title: "Identity verification" },
  { id: "image", label: "Image manipulation", type: "Image", title: "Image manipulation review" },
  { id: "audio", label: "Audio / voice deepfake", type: "Audio", title: "Audio authenticity review" },
  { id: "video", label: "Video deepfake", type: "Video", title: "Video authenticity review" },
  { id: "custom", label: "Custom investigation", type: "Custom", title: "" },
] as const;
const modules = [
  ["email_authentication", "Email headers · SPF/DKIM/DMARC", "Available"],
  ["url_analysis", "URL and domain analysis", "Available"],
  ["attachment_security", "Attachment validation and malware scan", "Available"],
  ["document_ocr", "Document extraction and OCR", "Available"],
  ["llm_context", "Evidence-grounded LLM context", "Experimental"],
  ["identity_provider", "Identity provider verification", "Coming Soon"],
  ["image_tamper", "Validated image tamper model", "Coming Soon"],
  ["audio_deepfake", "Audio spoof adapter", "Experimental"],
  ["video_deepfake", "Video deepfake adapter", "Experimental"],
] as const;
const sources = ["File upload", "Connected Gmail", "Manual indicators"];

export function NewInvestigationButton() {
  const router = useRouter();
  const [open, setOpen] = useState(false);
  const [template, setTemplate] = useState("phishing");
  const [subject, setSubject] = useState<string>(templates[0].title);
  const [caseType, setCaseType] = useState<string>(templates[0].type);
  const [selectedModules, setSelectedModules] = useState<string[]>(["email_authentication", "url_analysis", "attachment_security"]);
  const [selectedSources, setSelectedSources] = useState<string[]>(["File upload"]);
  const [state, setState] = useState<"idle" | "running" | "failed">("idle");
  const [message, setMessage] = useState("");

  function choose(value: string) {
    const next = templates.find(item => item.id === value) ?? templates[0];
    setTemplate(next.id); setSubject(next.title); setCaseType(next.type); setMessage("");
  }
  function toggle(value: string, current: string[], update: (values: string[]) => void) {
    update(current.includes(value) ? current.filter(item => item !== value) : [...current, value]);
  }

  async function launch(event: FormEvent) {
    event.preventDefault(); setState("running"); setMessage("");
    const response = await fetch("/api/investigations", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ subject, case_type: caseType, analysis_modules: selectedModules, evidence_sources: selectedSources }),
    });
    const body = await response.json();
    if (!response.ok) { setState("failed"); setMessage(body.detail ?? "Case creation failed"); return; }
    setState("idle"); setOpen(false); router.push(`/cases/${body.case.id}`); router.refresh();
  }

  return <>
    <button className="primary" onClick={() => setOpen(true)}><Sparkles size={16}/>New investigation</button>
    {open && <div className="investigation-overlay" role="presentation" onMouseDown={() => state !== "running" && setOpen(false)}>
      <form className="investigation-dialog panel" onSubmit={launch} onMouseDown={event => event.stopPropagation()}>
        <header><div><span className="eyebrow">NEW CASE</span><h2>Choose an investigation</h2><p>Create an empty case, then add Gmail, uploaded, or API evidence.</p></div><button type="button" onClick={() => setOpen(false)} aria-label="Close"><X size={17}/></button></header>
        <div className="investigation-options">{templates.map(item => <button type="button" className={template === item.id ? "selected" : ""} onClick={() => choose(item.id)} key={item.id}>{item.label}</button>)}</div>
        <div className="form-section form-grid"><label><span>Case title</span><input value={subject} onChange={event => setSubject(event.target.value)} placeholder="Describe what is being verified" minLength={3} maxLength={240} required/></label><label><span>Investigation type</span><input value={caseType} onChange={event => setCaseType(event.target.value)} minLength={2} maxLength={80} required disabled={template !== "custom"}/></label></div>
        <div className="investigation-config"><section><h3>Evidence sources</h3>{sources.map(source => <label key={source}><input type="checkbox" checked={selectedSources.includes(source)} onChange={() => toggle(source, selectedSources, setSelectedSources)}/><span>{source}</span></label>)}</section><section><h3>Analysis modules</h3>{modules.map(([id,label,status]) => <label key={id} className={status === "Coming Soon" ? "unavailable" : ""}><input type="checkbox" disabled={status === "Coming Soon"} checked={selectedModules.includes(id)} onChange={() => toggle(id, selectedModules, setSelectedModules)}/><span>{label}<em>{status}</em></span></label>)}</section></div>
        <div className="form-actions"><button className="primary" disabled={state === "running"}>{state === "running" ? "Creating…" : "Create case"}</button><span className={state === "failed" ? "form-error" : ""}>{message}</span></div>
      </form>
    </div>}
  </>;
}
