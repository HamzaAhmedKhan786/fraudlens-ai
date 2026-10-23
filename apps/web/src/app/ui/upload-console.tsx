"use client";

import { AlertTriangle, CheckCircle2, FileUp, RefreshCw, ShieldAlert } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import type { UploadList, UploadSummary } from "@/lib/backend";
import type { CasePage, CaseRow } from "@/lib/analytics-types";

function formatBytes(value: number) {
  return value < 1024 * 1024 ? `${(value / 1024).toFixed(1)} KB` : `${(value / 1024 / 1024).toFixed(1)} MB`;
}
export function UploadConsole() {
  const [cases, setCases] = useState<CaseRow[]>([]), [uploads, setUploads] = useState<UploadSummary[]>([]);
  const [caseId, setCaseId] = useState(""), [query, setQuery] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [state, setState] = useState<"idle" | "uploading" | "success" | "error">("idle");
  const [progress, setProgress] = useState(0), [dragging, setDragging] = useState(false);
  const [message, setMessage] = useState(""), [queueError, setQueueError] = useState("");
  const xhr = useRef<XMLHttpRequest | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const controller = new AbortController();
    const timer = setTimeout(() => {
      fetch(`/api/cases/search?q=${encodeURIComponent(query)}&page_size=50`, { signal: controller.signal })
        .then(async response => { if (!response.ok) throw new Error(); return await response.json() as CasePage; })
        .then(data => { setCases(data.items); setCaseId(current => current || data.items[0]?.id || ""); })
        .catch(() => { if (!controller.signal.aborted) setQueueError("Case choices could not be loaded."); });
    }, 200);
    return () => { clearTimeout(timer); controller.abort(); };
  }, [query]);
  const refresh = useCallback(async () => {
    try {
      const response = await fetch("/api/uploads");
      if (!response.ok) throw new Error();
      setUploads(((await response.json()) as UploadList).items); setQueueError("");
    } catch { setQueueError("The processing queue could not be loaded. Please refresh."); }
  }, []);
  useEffect(() => {
    void refresh();
    const timer = setInterval(() => { if (!document.hidden) void refresh(); }, 10000);
    return () => { clearInterval(timer); xhr.current?.abort(); };
  }, [refresh]);
  function chooseFile(candidate: File | null) {
    if (!candidate) return;
    if (!/\.(eml|pdf|docx|txt|png|jpe?g)$/i.test(candidate.name) || candidate.size > 50 * 1024 * 1024) {
      setState("error"); setMessage("Choose EML, PDF, DOCX, TXT, PNG or JPEG up to 50 MB."); setFile(null); return;
    }
    setFile(candidate); setMessage(""); setState("idle");
  }
  function submit(event: React.FormEvent) {
    event.preventDefault();
    if (!file || !caseId || state === "uploading") return;
    setState("uploading"); setMessage(""); setProgress(0);
    const form = new FormData(); form.set("case_id", caseId); form.set("file", file);
    const request = new XMLHttpRequest(); xhr.current = request;
    request.open("POST", "/api/uploads");
    request.upload.onprogress = event => { if (event.lengthComputable) setProgress(Math.round(event.loaded / event.total * 100)); };
    request.onload = () => {
      let result: { status?: string; filename?: string; detail?: string } = {};
      try { result = JSON.parse(request.responseText); } catch { /* Non-JSON proxy errors. */ }
      if (request.status >= 200 && request.status < 300) {
        setState("success"); setMessage(`Evidence ${result.status?.toLowerCase()}: ${result.filename}`);
        setFile(null); if (fileInput.current) fileInput.current.value = ""; void refresh();
      } else { setState("error"); setMessage(typeof result.detail === "string" ? result.detail : "Upload failed. Check file validation, permissions, and service availability."); }
    };
    request.onerror = () => { setState("error"); setMessage("Upload connection failed. Your file has not been confirmed as received."); };
    request.timeout = 180000; request.ontimeout = () => { setState("error"); setMessage("Upload timed out. Refresh the queue before retrying."); };
    request.send(form);
  }
  async function retry(id: string) {
    try {
      const response = await fetch(`/api/uploads/${encodeURIComponent(id)}/retry`, { method: "POST" });
      if (!response.ok) throw new Error();
      await refresh();
    } catch { setQueueError("Retry could not be scheduled. Check the evidence state and permissions."); }
  }
  return <div className="intake-grid">
    <form className="panel upload-form" onSubmit={submit}>
      <div className="panel-head"><div><h2>Bring your evidence into focus</h2><p>Select a case, then upload a supported file</p></div><FileUp size={18}/></div>
      <div className="form-section form-grid-single"><label><span>Find a case</span><input value={query} onChange={e => setQuery(e.target.value)} placeholder="Search case ID or subject" aria-label="Find a case for upload"/></label><label><span>Investigation</span><select value={caseId} onChange={e => setCaseId(e.target.value)} required aria-label="Evidence investigation"><option value="">Choose a case</option>{cases.map(item => <option key={item.id} value={item.id}>{item.id} · {item.subject}</option>)}</select></label>
      <label className={`file-drop ${dragging ? "dragging" : ""}`} onDragOver={event => { event.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={event => { event.preventDefault(); setDragging(false); chooseFile(event.dataTransfer.files[0] ?? null); }}><input ref={fileInput} type="file" accept=".eml,.pdf,.docx,.txt,.png,.jpg,.jpeg" onChange={e => chooseFile(e.target.files?.[0] ?? null)} aria-label="Choose evidence file"/><FileUp size={32}/><strong>{file?.name ?? "Drop evidence here, or browse files"}</strong><small>EML, PDF, DOCX, TXT, PNG, JPEG · Up to 50 MB</small>{file && <small>{formatBytes(file.size)}</small>}</label>
      <div className="security-notes"><span><CheckCircle2 size={15}/>Content validation</span><span><ShieldAlert size={15}/>Scan status tracked</span><span><CheckCircle2 size={15}/>SHA-256 fingerprint</span></div></div>
      {state === "uploading" && <div className="upload-progress" role="status"><label>{progress < 100 ? `Uploading ${progress}%` : "Transfer complete. Waiting for scan and processing…"}</label><progress value={progress} max={100} aria-label="File transfer progress"/></div>}
      <div className="form-actions"><button className="primary" disabled={!file || !caseId || state === "uploading"}><FileUp size={14}/>{state === "uploading" ? "Processing…" : "Upload evidence"}</button>{message && <span role="status" className={state === "error" ? "form-error" : ""}>{message}</span>}</div>
    </form>
    <section className="panel upload-list"><div className="panel-head"><div><h2>Evidence processing queue</h2><p>{uploads.length} recent records · Live scan and processing states</p></div><button onClick={() => void refresh()} aria-label="Refresh uploads"><RefreshCw size={15}/></button></div>
    {queueError && <div className="inline-error" role="alert">{queueError}</div>}
    {uploads.map(item => <article className="upload-item" key={item.id}><div className={`upload-state ${item.status.toLowerCase()}`}>{["QUARANTINED", "DEAD_LETTER"].includes(item.status) ? <AlertTriangle size={17}/> : <CheckCircle2 size={17}/>}</div><div><strong>{item.filename}</strong><span>{item.case_id} · {formatBytes(item.size_bytes)} · {item.detected_content_type}</span><span className="quiet-label">{item.status.replaceAll("_", " ")}</span><small>Scan: {item.scan_status} · Attempt {item.processing_attempts}</small><small>SHA-256 {item.sha256.slice(0, 20)}…</small>{item.error && <em>{item.error}</em>}</div><div>{item.object_available && item.status !== "QUARANTINED" && <a href={`/api/uploads/${item.id}/content`}>Download</a>}{["RETRY_PENDING", "FAILED"].includes(item.status) && <button onClick={() => void retry(item.id)}>Retry</button>}</div></article>)}
    {!uploads.length && !queueError && <div className="empty-state"><FileUp size={28}/><h3>Your evidence starts here</h3><p>Upload a file to see its validation, scan, and processing status.</p></div>}</section>
  </div>;
}
