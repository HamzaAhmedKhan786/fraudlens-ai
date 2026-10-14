"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { CaseDetail } from "@/lib/backend";

export function CaseWorkflow({ item }: { item: CaseDetail }) {
  const router = useRouter();
  const [assignee, setAssignee] = useState(item.assignee ?? "");
  const [comment, setComment] = useState("");
  const [message, setMessage] = useState("");
  async function update(payload: Record<string, string | null>) {
    const response = await fetch(`/api/cases/${encodeURIComponent(item.id)}`, { method:"PATCH", headers:{"Content-Type":"application/json"}, body:JSON.stringify(payload) });
    setMessage(response.ok ? "Case workflow updated and audited." : "Update failed.");
    if (response.ok) router.refresh();
  }
  async function addComment() {
    if (!comment.trim()) return;
    const response = await fetch(`/api/cases/${encodeURIComponent(item.id)}/comments`, { method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({body:comment}) });
    if (response.ok) { setComment(""); setMessage("Comment added."); router.refresh(); }
  }
  return <section className="panel settings-form"><div className="panel-head"><div><h2>Case workflow</h2><p>Assignment, escalation, review and final disposition</p></div></div><div className="form-section form-grid"><label><span>Assignee</span><input value={assignee} onChange={e=>setAssignee(e.target.value)} placeholder="analyst@example.com"/></label><label><span>Status</span><select defaultValue={item.status} onChange={e=>void update({status:e.target.value})}><option>OPEN</option><option>UNDER_REVIEW</option><option>ESCALATED</option><option>RESOLVED</option></select></label></div><div className="form-actions"><button className="primary" onClick={()=>void update({assignee:assignee || null})}>Assign case</button><button onClick={()=>void update({disposition:"CONFIRMED_FRAUD"})}>Confirm fraud</button><button onClick={()=>void update({disposition:"FALSE_POSITIVE"})}>False positive</button><button onClick={()=>void update({disposition:"INCONCLUSIVE"})}>Inconclusive</button>{message&&<span>{message}</span>}</div><div className="form-section"><h2>Investigation notes</h2><textarea value={comment} onChange={e=>setComment(e.target.value)} maxLength={4000} placeholder="Add an evidence-grounded analyst note…"/><button className="primary inline-action" onClick={()=>void addComment()}>Add comment</button>{item.comments.map(note=><article className="notice-box" key={note.id}><strong>{note.author}</strong> · {new Date(note.created_at).toLocaleString()}<p>{note.body}</p></article>)}</div></section>;
}
