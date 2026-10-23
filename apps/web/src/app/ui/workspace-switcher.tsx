"use client";
import { useEffect, useState } from "react";
import type { WorkspaceSummary } from "@/lib/backend";
export function WorkspaceSwitcher() {
  const [items, setItems] = useState<WorkspaceSummary[]>([]), [selected, setSelected] = useState("");
  const [busy, setBusy] = useState(false), [error, setError] = useState("");
  useEffect(() => {
    const controller = new AbortController();
    Promise.all([
      fetch("/api/workspaces", { signal: controller.signal }).then(r => r.ok ? r.json() : []),
      fetch("/api/session", { signal: controller.signal }).then(r => r.ok ? r.json() : null),
    ]).then(([workspaces, session]) => {
      setItems(workspaces); setSelected(session?.tenant_id ?? "");
    }).catch(() => {});
    return () => controller.abort();
  }, []);
  async function choose(id: string) {
    setBusy(true);
    try {
      const response = await fetch("/api/workspaces/select", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ id }) });
      if (!response.ok) throw new Error();
      location.reload();
    } catch { setError("Workspace switch failed."); setBusy(false); }
  }
  return <div className="workspace"><span>Workspace</span><select disabled={busy} aria-label="Active workspace" value={selected} onChange={e => void choose(e.target.value)}>
    {!items.some(item => item.id === selected) && <option value={selected}>{selected || "Loading workspace…"}</option>}
    {items.map(item => <option key={item.id} value={item.id}>{item.name} · {item.role}</option>)}
  </select><a href="/workspaces">Manage workspaces</a>{error && <small role="alert">{error}</small>}</div>;
}
