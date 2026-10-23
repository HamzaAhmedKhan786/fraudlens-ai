"use client";
import { Play, ShieldCheck } from "lucide-react";
import { useRouter } from "next/navigation";
import { useState } from "react";
export function CaseActions({ caseId }: { caseId: string }) {
  const [busy, setBusy] = useState(false), [review, setReview] = useState(false);
  const [reason, setReason] = useState(""), [message, setMessage] = useState("");
  const router = useRouter();
  async function action(path: string, payload?: object) {
    setBusy(true); setMessage("");
    try {
      const response = await fetch(`/api/cases/${encodeURIComponent(caseId)}/${path}`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        ...(payload ? { body: JSON.stringify(payload) } : {}),
      });
      if (!response.ok) throw new Error("Action failed. Check permissions and evidence availability.");
      setMessage(path === "reviews" ? "Verification requested and recorded." : "Analysis completed.");
      setReview(false); router.refresh();
    } catch (err) { setMessage(err instanceof Error ? err.message : "Request failed."); }
    finally { setBusy(false); }
  }
  return <section className="panel"><div className="case-actions"><button className="primary" disabled={busy} onClick={() => void action("investigate")}><Play size={13}/>{busy ? "Processing…" : "Run analysis"}</button><button className="secondary" onClick={() => setReview(value => !value)}><ShieldCheck size={13}/>Request verification</button></div>
    {review && <form className="form-section" onSubmit={e => { e.preventDefault(); void action("reviews", { request_type: "VERIFICATION", reason }); }}><label htmlFor="verification-reason">Reason for review</label><textarea id="verification-reason" minLength={10} maxLength={4000} required value={reason} onChange={e => setReason(e.target.value)}/><button className="primary inline-action" disabled={busy || reason.trim().length < 10}>Submit review request</button></form>}
    {message && <p className="notice-box" role="status">{message}</p>}
  </section>;
}
