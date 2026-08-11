"use client";

import { useState } from "react";

export function SettingsForm() {
  const [saved, setSaved] = useState(false);
  const [settings, setSettings] = useState({ humanReview: true, llmNarrative: false, critical: "80", retention: "180" });
  function update(key: keyof typeof settings, value: string | boolean) { setSaved(false); setSettings(current => ({ ...current, [key]: value })); }
  return <section className="panel settings-form"><div className="form-section"><h2>Investigation controls</h2><label className="switch-row"><span><strong>Mandatory human review</strong><small>Prevent automated final fraud decisions.</small></span><input type="checkbox" checked={settings.humanReview} onChange={event => update("humanReview", event.target.checked)}/></label><label className="switch-row"><span><strong>LLM narrative</strong><small>Use a configured provider only for cited summaries.</small></span><input type="checkbox" checked={settings.llmNarrative} onChange={event => update("llmNarrative", event.target.checked)}/></label></div><div className="form-section form-grid"><label><span>Critical risk threshold</span><input type="number" min="0" max="100" value={settings.critical} onChange={event => update("critical", event.target.value)}/></label><label><span>Evidence retention (days)</span><input type="number" min="1" value={settings.retention} onChange={event => update("retention", event.target.value)}/></label></div><div className="form-actions"><button className="primary" onClick={() => setSaved(true)}>Save workspace settings</button>{saved && <span>Saved for this browser session.</span>}</div></section>;
}

