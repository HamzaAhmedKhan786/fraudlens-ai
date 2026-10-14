"use client";

import { useState } from "react";
import type { PolicyDefinition } from "@/lib/backend";

export function PolicyConsole({ initial }: { initial: PolicyDefinition[] }) {
  const [policies, setPolicies] = useState(initial);
  const [message, setMessage] = useState("");
  async function save(policy: PolicyDefinition) {
    setMessage("Saving policy…");
    const response = await fetch(`/api/policies/${encodeURIComponent(policy.id)}`, { method:"PUT", headers:{"Content-Type":"application/json"}, body:JSON.stringify({enabled:policy.enabled, threshold:policy.threshold}) });
    if (!response.ok) { setMessage("Policy update failed."); return; }
    const saved = await response.json() as PolicyDefinition;
    setPolicies(current=>current.map(item=>item.id===saved.id?saved:item));
    setMessage("Policy version saved and audit event recorded.");
  }
  return <section className="panel data-panel"><div className="records"><div className="record policy-record record-head"><span>Policy</span><span>Version</span><span>Threshold</span><span>State</span></div>{policies.map((policy,index)=><div className="record policy-record" key={policy.id}><span><strong>{policy.name}</strong><small>{policy.description}</small></span><span>{policy.version}</span><span><input type="number" min="0" max="100" value={policy.threshold} onChange={e=>setPolicies(current=>current.map((item,i)=>i===index?{...item,threshold:Number(e.target.value)}:item))}/>%</span><span><label><input type="checkbox" checked={policy.enabled} onChange={e=>setPolicies(current=>current.map((item,i)=>i===index?{...item,enabled:e.target.checked}:item))}/> Enabled</label><button onClick={()=>void save(policy)}>Save</button></span></div>)}</div>{message&&<div className="notice-box">{message}</div>}</section>;
}
