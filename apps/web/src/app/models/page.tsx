import { backendFetch, type ModelHealth } from "@/lib/backend";
import { SectionHeader, WorkspaceShell } from "../ui/workspace-shell";

export default async function ModelsPage() {
  const models = await backendFetch<ModelHealth[]>("/models/health").catch(() => []);
  return <WorkspaceShell><div className="content section-page"><SectionHeader eyebrow="MODEL OPERATIONS" title="Model health" description="Runtime readiness distinguishes operational detectors from adapters awaiting validated models."/><div className="cards-grid">{models.map(model => <article className="panel feature-card" key={model.id}><div className="feature-top"><span className={`status-dot ${model.status.toLowerCase()}`}/><em>{model.status.replaceAll("_", " ")}</em><b>{model.latency_ms === null ? "—" : `${model.latency_ms} ms`}</b></div><h2>{model.name}</h2><p>{model.detail}</p><small>{model.provider} · checked {new Date(model.last_checked).toLocaleTimeString()}</small></article>)}</div></div></WorkspaceShell>;
}
