"use client";

import { useEffect, useState } from "react";
import type { WorkspaceSettings } from "@/lib/backend";

const initial: WorkspaceSettings = { mandatory_human_review: true, llm_narrative_enabled: false, critical_risk_threshold: 80, evidence_retention_days: 180, updated_at: null };

export function SettingsForm() {
  const [settings, setSettings] = useState(initial);
  const [message, setMessage] = useState("Loading workspace settings…");
  useEffect(() => { void fetch("/api/settings").then(r => r.json()).then(value => { setSettings(value); setMessage(""); }); }, []);
  async function save() {
    setMessage("Saving…");
    const response = await fetch("/api/settings", { method: "PUT", headers: { "Content-Type": "application/json" }, body: JSON.stringify(settings) });
    if (!response.ok) { setMessage("Unable to save settings."); return; }
    setSettings(await response.json()); setMessage("Workspace settings saved and audited.");
  }
  return <section className="panel settings-form"><div className="form-section"><h2>Investigation controls</h2><label className="switch-row"><span><strong>Mandatory human review</strong><small>Prevent automated final fraud decisions.</small></span><input type="checkbox" checked={settings.mandatory_human_review} onChange={e => setSettings({...settings, mandatory_human_review:e.target.checked})}/></label><label className="switch-row"><span><strong>LLM narrative</strong><small>Use a configured provider only for cited summaries.</small></span><input type="checkbox" checked={settings.llm_narrative_enabled} onChange={e => setSettings({...settings, llm_narrative_enabled:e.target.checked})}/></label></div><div className="form-section form-grid"><label><span>Critical risk threshold</span><input type="number" min="0" max="100" value={settings.critical_risk_threshold} onChange={e => setSettings({...settings, critical_risk_threshold:Number(e.target.value)})}/></label><label><span>Evidence retention (days)</span><input type="number" min="1" max="3650" value={settings.evidence_retention_days} onChange={e => setSettings({...settings, evidence_retention_days:Number(e.target.value)})}/></label></div><div className="form-actions"><button className="primary" onClick={() => void save()}>Save workspace settings</button>{message && <span>{message}</span>}</div></section>;
}
