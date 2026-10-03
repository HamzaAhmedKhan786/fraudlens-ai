"use client";

import { AlertTriangle, CheckCircle2, FileUp, RefreshCw, ShieldAlert } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import type { CaseSummary, UploadList, UploadSummary } from "@/lib/backend";

function formatBytes(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

export function UploadConsole() {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [uploads, setUploads] = useState<UploadSummary[]>([]);
  const [caseId, setCaseId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  const refresh = useCallback(async () => {
    const [caseResponse, uploadResponse] = await Promise.all([
      fetch("/api/cases"),
      fetch("/api/uploads"),
    ]);
    if (caseResponse.ok) {
      const items = (await caseResponse.json()) as CaseSummary[];
      setCases(items);
      setCaseId(current => current || items[0]?.id || "");
    }
    if (uploadResponse.ok) {
      setUploads(((await uploadResponse.json()) as UploadList).items);
    }
  }, []);

  useEffect(() => {
    void refresh();
    const timer = window.setInterval(() => void refresh(), 5000);
    return () => window.clearInterval(timer);
  }, [refresh]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !caseId) return;
    setState("uploading");
    setMessage("");
    const form = new FormData();
    form.set("case_id", caseId);
    form.set("file", file);
    const response = await fetch("/api/uploads", { method: "POST", body: form });
    const result = await response.json();
    if (!response.ok) {
      setState("error");
      setMessage(result.detail ?? "Upload failed");
      return;
    }
    setState("success");
    setMessage(`Evidence ${result.status.toLowerCase()}: ${result.filename}`);
    setFile(null);
    await refresh();
  }

  async function retry(id: string) {
    await fetch(`/api/uploads/${id}/retry`, { method: "POST" });
    await refresh();
  }

  return <div className="intake-grid">
    <form className="panel upload-form" onSubmit={submit}>
      <div className="panel-head"><div><h2>Submit evidence</h2><p>Validated, scanned, hashed, and stored immutably</p></div><FileUp size={18}/></div>
      <div className="form-section form-grid-single"><label><span>Fraud case</span><select value={caseId} onChange={event => setCaseId(event.target.value)} required>{cases.map(item => <option key={item.id} value={item.id}>{item.id} · {item.subject}</option>)}</select></label><label className="file-drop"><input type="file" accept=".eml,.pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={event => setFile(event.target.files?.[0] ?? null)} required/><FileUp size={24}/><strong>{file?.name ?? "Choose an evidence file"}</strong><small>EML, PDF, DOCX, TXT, PNG or JPEG · maximum 50 MB</small></label><div className="security-notes"><span><CheckCircle2 size={14}/>SHA-256 deduplication</span><span><ShieldAlert size={14}/>ClamAV quarantine</span><span><CheckCircle2 size={14}/>Content-based MIME validation</span></div></div>
      <div className="form-actions"><button className="primary" disabled={!file || !caseId || state === "uploading"}>{state === "uploading" ? "Scanning and processing…" : "Upload evidence"}</button>{message && <span className={state === "error" ? "form-error" : ""}>{message}</span>}</div>
    </form>
    <section className="panel upload-list"><div className="panel-head"><div><h2>Processing queue</h2><p>{uploads.length} recent evidence items</p></div><button onClick={() => void refresh()} aria-label="Refresh uploads"><RefreshCw size={15}/></button></div>{uploads.map(item => <article className="upload-item" key={item.id}><div className={`upload-state ${item.status.toLowerCase()}`}>{item.status === "QUARANTINED" || item.status === "DEAD_LETTER" ? <AlertTriangle size={16}/> : <CheckCircle2 size={16}/>}</div><div><strong>{item.filename}</strong><span>{item.case_id} · {formatBytes(item.size_bytes)} · {item.detected_content_type}</span><small>Scan: {item.scan_status} · attempt {item.processing_attempts} · SHA {item.sha256.slice(0,12)}</small>{item.error && <em>{item.error}</em>}</div><div>{item.object_available && item.status !== "QUARANTINED" && <a href={`/api/uploads/${item.id}/content`}>Download</a>}{["RETRY_PENDING","FAILED"].includes(item.status) && <button onClick={() => void retry(item.id)}>Retry</button>}</div></article>)}{!uploads.length && <div className="empty-state">No evidence has been uploaded.</div>}</section>
  </div>;
}

